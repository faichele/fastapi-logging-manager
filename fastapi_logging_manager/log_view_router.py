import os
import asyncio

from typing import Callable, Generator
from pathlib import Path

from fastapi import APIRouter, Request, FastAPI, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect, WebSocketState

from .logger_manager import logger_manager

# set template and static file directories for Jinja
base_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(base_dir, "templates")))


async def log_reader(log_file: str, n: int = 5) -> list[str]:
    """Log reader

    Args:
        log_file (str): Path to log file.
        n (int, optional): Number of lines to read from file. Defaults to 5.

    Returns:
        list[str]: List containing last n-lines in log file with html tags.
    """
    log_lines: list[str] = []
    if os.path.exists(f"{log_file}"):
        with open(f"{log_file}", "r", encoding="utf-8", errors="replace") as file:
            for line in file.readlines()[-n:]:
                if "ERROR" in line:
                    log_lines.append(f'<span class="text-red-400">{line}</span><br/>')
                elif "WARNING" in line:
                    log_lines.append(f'<span class="text-orange-300">{line}</span><br/>')
                else:
                    log_lines.append(f"{line}<br/>")

    return log_lines


def _resolve_logfile_for_logger(logger_name: str | None) -> str | None:
    """Return logfile path for a given logger name (if known)."""
    if not logger_name:
        return None

    # We use the internal registry because it holds the Logger objects.
    logger = logger_manager._loggers_with_logfiles.get(logger_name)  # type: ignore[attr-defined]
    if not logger:
        return None

    for handler in getattr(logger, "handlers", []):
        file_name = getattr(handler, "baseFilename", None)
        if isinstance(file_name, str) and file_name:
            return file_name

    return None


def create_log_view_router(
    app: FastAPI,
    prefix: str = "/api/settings",
    get_db: Callable[[], Generator[Session, None, None]] | None = None,
    *,
    enable_templates: bool = False,
    templates_directory: str | Path | None = None,
    custom_template_name: str | None = None,
) -> APIRouter:

    # Expose packaged templates for debugging (optional). Point to the package templates dir.
    app.mount("/templates/log_viewer", StaticFiles(directory=str(Path(base_dir, "templates"))), name="templates")

    router = APIRouter(prefix=prefix, tags=["log_viewer"])

    @router.get("", include_in_schema=False)
    async def get_no_slash(request: Request):
        # Browser landen je nach Setup oft auf `/log_viewer` (ohne Slash).
        # Damit die eigentliche HTML-Route (`/`) greift, redirecten wir auf `/log_viewer/`.
        return RedirectResponse(url=str(request.url) + "/")

    @router.get("/", response_class=HTMLResponse, include_in_schema=True)
    async def get(request: Request):
        """Log file viewer"""
        context = {
            "title": "FastAPI Streaming Log Viewer over WebSockets",
            "loggers": logger_manager.loggers_with_logfiles,
        }
        return templates.TemplateResponse("log_viewer.html", {"request": request, "context": context})

    @router.get("/logs/logger_names", response_class=JSONResponse)
    async def get_logger_names(request: Request):
        return sorted(logger_manager.loggers_with_logfiles)

    @app.websocket("/ws/log")
    async def websocket_endpoint_log(websocket: WebSocket) -> None:
        await websocket.accept()

        # optional query param supplied by frontend: ws://.../ws/log?logger=<name>
        logger_name = websocket.query_params.get("logger")
        logfile = _resolve_logfile_for_logger(logger_name)

        # fallback: try app.log if present
        if logfile is None:
            logfile = _resolve_logfile_for_logger("app")

        try:
            while True:
                await asyncio.sleep(1)
                if logfile is None:
                    await websocket.send_text("No logfile configured for selected logger.")
                    continue

                logs = await log_reader(logfile, n=30)
                await websocket.send_text("".join(logs))
        except WebSocketDisconnect:
            # Client disconnected (browser tab closed / network drop). Nothing to do.
            return
        except Exception as e:
            print(e)
        finally:
            # Avoid RuntimeError: "Cannot call send once a close message has been sent."
            try:
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
            except RuntimeError:
                # Close frame already sent.
                pass

    return router