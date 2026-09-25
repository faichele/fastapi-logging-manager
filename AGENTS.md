# AGENTS.md — fastapi-logging-manager

## Zweck

Dieses Paket liefert einen wiederverwendbaren `LoggerManager` und optional einen FastAPI-Router
zum Anzeigen von Logdateien. Der Kern ist ein kleines, eigenstaendiges Python-Paket fuer Logging-
Konfiguration und Log-Viewer.

## Wichtige Regeln

- Oeffentliche Exporte laufen ueber `fastapi_logging_manager.__init__`.
- `logger_manager` ist die vorgesehene Singleton-Instanz; neue Nutzung sollte darauf aufbauen.
- Der Router in `log_view_router.py` darf nur ergaenzt werden, wenn sich das oeffentliche Verhalten
  des Log-Viewers bewusst aendert.
- Paketdaten wie `templates/*.html` und `templates/README.md` muessen in der Distribution bleiben.

## Projektstruktur

- `fastapi_logging_manager/logger_manager.py`: Logger-Konfiguration, Defaults aus Env-Variablen,
  vordefinierte Logger-Helfer
- `fastapi_logging_manager/log_view_router.py`: FastAPI-Router und WebSocket-Log-Viewer
- `fastapi_logging_manager/templates/`: HTML-Template fuer den Viewer
- `tests/`: Basis- und Packaging-Tests

## Verhalten

- Konfiguration erfolgt ueber `FASTAPI_LOGGER_*`-Umgebungsvariablen mit sinnvollen Defaults.
- `get_logger()` darf bestehende Logger nicht still neu konfigurieren, wenn sie bereits registriert
  sind.
- Datei-Logging legt das Verzeichnis bei Bedarf lazy an.
- Datei-Logger verwenden `RotatingFileHandler`; automatische Rotation ist optional, manuelle
  Rotation erfolgt ueber `rotate_logger()` oder `rotate_all_loggers()`.
- Der Router greift auf registrierte Logger mit Datei-Handlern zurueck und fallt bei Bedarf auf
  `app` zurück.

## Vorgehen bei Aenderungen

1. Nur die betroffene Logging- oder Router-Logik aendern.
2. Falls neue oeffentliche Helfer hinzukommen, sie in `__init__.py` exportieren.
3. Tests bei Verhaltensaenderungen oder Packaging-Aenderungen erweitern.

## Qualitaetssicherung

- `pytest`
- `ruff check .`
- `black .`
- Manuell pruefen, dass die Templates weiterhin mitgepackt werden

## Nicht tun

- Keine Engines, Sessions oder Datenbanklogik einbauen.
- Keine stillen Fallbacks fuer Fehlerpfade ergaenzen, wenn sie das Verhalten verschleiern.
- Keine Dateien unter `__pycache__` oder IDE-Metadaten anfassen.
