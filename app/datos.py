"""Carga, validación y análisis geográfico de las dependencias (pandas + NumPy)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
CENTRO = (16.8531, -99.8237)           # referencia para medir dispersión (Acapulco)
LIMITES_GUERRERO = {"lat": (16.3, 18.9), "lon": (-102.2, -98.0)}
R_TIERRA_KM = 6371.0088
CARRERAS = ["Ing. Sistemas Computacionales", "Lic. Administración", "Ing. Gestión Empresarial",
            "Ing. Bioquímica", "Ing. Electromecánica", "Contador Público", "Arquitectura"]


def cargar_dependencias(ruta: Path = DATA / "dependencias.json") -> pd.DataFrame:
    """Un DataFrame con una fila por SEDE (una dependencia puede tener varias)."""
    filas = []
    for d in json.loads(Path(ruta).read_text(encoding="utf-8")):
        base = {k: v for k, v in d.items() if k != "sedes"}
        for n, s in enumerate(d["sedes"], start=1):
            filas.append({**base, "sede_n": n, "sede": s["nombre"], "lat": s["lat"], "lon": s["lon"]})
    df = pd.DataFrame(filas)
    con_sede = df["sede"].notna()
    df["etiqueta"] = df["nombre"].where(~con_sede, df["nombre"] + " (" + df["sede"].fillna("") + ")")
    return df


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en línea recta (km). Vectorizada: acepta escalares o arreglos."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(x, dtype=float)) for x in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(a))


def cercanas(df: pd.DataFrame, lat: float, lon: float, limite: int | None = 10) -> pd.DataFrame:
    """Sedes ordenadas por distancia a (lat, lon), con la columna distancia_km."""
    out = df.assign(distancia_km=haversine_km(lat, lon, df["lat"], df["lon"]).round(2))
    out = out.sort_values("distancia_km", kind="stable")
    return out if limite is None else out.head(limite)


def validar(df: pd.DataFrame) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía = datos válidos)."""
    errores = []
    for col in ("id", "nombre", "lat", "lon"):
        if df[col].isna().any():
            errores.append(f"Columna '{col}' tiene valores vacíos.")
    if df.duplicated(["id", "sede_n"]).any():
        errores.append("Hay sedes repetidas (id, sede_n).")
    fuera = df[~df["lat"].between(*LIMITES_GUERRERO["lat"]) | ~df["lon"].between(*LIMITES_GUERRERO["lon"])]
    errores += [f"{r.etiqueta}: coordenadas fuera de Guerrero ({r.lat}, {r.lon})." for r in fuera.itertuples()]
    redondeo = df.assign(_la=df["lat"].round(5), _lo=df["lon"].round(5))
    dup = df[redondeo.duplicated(["_la", "_lo"], keep=False)]
    errores += [f"{r.etiqueta}: comparte coordenadas con otra sede." for r in dup.itertuples()]
    return errores


def con_atipicas(df: pd.DataFrame, centro=CENTRO) -> pd.DataFrame:
    """Agrega distancia_centro_km y marca valores atípicos (regla del rango intercuartílico)."""
    out = df.assign(distancia_centro_km=haversine_km(centro[0], centro[1], df["lat"], df["lon"]).round(2))
    q1, q3 = out["distancia_centro_km"].quantile([.25, .75])
    out["atipica"] = out["distancia_centro_km"] > q3 + 1.5 * (q3 - q1)
    return out


def a_registros(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de dicts JSON-seguros (NaN pasa a None)."""
    return df.astype(object).where(df.notna(), None).to_dict("records")
