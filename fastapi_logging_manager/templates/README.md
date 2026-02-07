Dieses Verzeichnis enthält die Jinja2-Templates, die vom Modul `fastapi_logging_manager` zur Laufzeit geladen werden.

Wichtig:
- Dateien hier drin müssen beim Packaging enthalten sein.
- Das wird über `pyproject.toml` (`[tool.setuptools.package-data]`) und `MANIFEST.in` abgesichert.
