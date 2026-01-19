# fastapi-logger-manager

Wiederverwendbarer LoggerManager als kleines Python-Paket, gedacht für FastAPI- und andere Python-Anwendungen.

## Installation

```bash
pip install fastapi-logger-manager
```

## Schnelleinstieg

```python
from fastapi_logger_manager import logger_manager

logger = logger_manager.get_app_logger()
logger.info("App started")
```

Siehe Docstrings und Quelltext für weitere Details (vordefinierte Logger, Umgebungsvariablen, etc.).

