# Servicio Social Tec (avance)
Plataforma para elegir dependencia de servicio social (TecNM Acapulco). FastAPI + Jinja2 + Leaflet.

    docker compose up --build      # http://localhost:8000
    # sin Docker: pip install -r requirements.txt && uvicorn app.main:app --reload

- `data/dependencias.json`: 30 dependencias del PDF; área, carreras y convenio están en `null` hasta verificarlos; las coordenadas (`sedes`) ya están capturadas, pendientes de verificar.
- `data/calendario.json`: calendario Nov 2026 - May 2027 (2 fechas corregidas, ver /proceso).

## Fase 2: datos y análisis
    pip install -r requirements-dev.txt
    pytest                                   # pruebas
    jupyter lab notebooks/                   # exploración (01_exploracion.ipynb)
    python -m scripts.faltantes generar      # crea/actualiza data/faltantes.csv
    python -m scripts.faltantes fusionar --dry-run   # revisa avisos; sin --dry-run escribe el JSON

- `app/datos.py`: carga a pandas (una fila por sede), validación, haversine vectorizada, valores atípicos.
- `GET /api/cercanas?lat=&lon=&limite=`: sedes más cercanas en línea recta.
- Llena `data/faltantes.csv` en una hoja de cálculo (celda vacía = no cambia nada) y fusiónalo.
