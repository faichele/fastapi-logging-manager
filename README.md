# fastapi-logger-manager

Wiederverwendbarer LoggerManager als kleines Python-Paket, gedacht für FastAPI- und andere Python-Anwendungen.

## Installation

```bash
pip install fastapi-logger-manager
```

## Schnelleinstieg

```python
from fastapi_logging_manager import logger_manager

logger = logger_manager.get_app_logger()
logger.info("App started")
```

Siehe Docstrings und Quelltext für weitere Details (vordefinierte Logger, Umgebungsvariablen, etc.).

## Log-Rotation

Datei-Logger verwenden intern `RotatingFileHandler`. Die automatische Rotation ist standardmäßig
deaktiviert, damit bestehendes Verhalten erhalten bleibt. Sie kann über Umgebungsvariablen aktiviert
werden:

```dotenv
FASTAPI_LOGGER_ROTATION_ENABLED=true
FASTAPI_LOGGER_MAX_BYTES=10485760
FASTAPI_LOGGER_BACKUP_COUNT=5
```

Alternativ kann sie pro Logger konfiguriert werden:

```python
logger = logger_manager.get_logger(
    "worker",
    to_file=True,
    rotation_enabled=True,
    max_bytes=10 * 1024 * 1024,
    backup_count=5,
)
```

Eine manuelle Rotation und Statusabfrage ist ebenfalls möglich:

```python
logger_manager.rotate_logger("worker")
logger_manager.rotate_all_loggers()
status = logger_manager.rotation_status("worker")
```

Auch bei deaktivierter automatischer Rotation kann ein Datei-Logger manuell rotiert werden.
