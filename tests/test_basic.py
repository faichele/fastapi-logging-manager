from __future__ import annotations

from importlib.resources import files


def test_template_is_packaged() -> None:
    path = files("fastapi_logging_manager").joinpath("templates", "log_viewer.html")
    assert path.is_file(), "Expected templates/log_viewer.html to be packaged inside fastapi_logging_manager"
    # tiny sanity check: file isn't empty
    assert path.read_text(encoding="utf-8").strip().startswith("<!DOCTYPE html>")
