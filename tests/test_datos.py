import pytest
from fastapi.testclient import TestClient

from app import datos
from app.main import app

df = datos.cargar_dependencias()


def test_una_fila_por_sede():
    assert len(df) == 35 and df["id"].nunique() == 30


def test_datos_actuales_son_validos():
    assert datos.validar(df) == []


def test_validar_detecta_coordenadas_fuera_de_guerrero():
    malo = df.copy(); malo.loc[0, "lat"] = 19.43
    assert any("fuera de Guerrero" in e for e in datos.validar(malo))


def test_haversine_un_grado_de_longitud_en_el_ecuador():
    assert datos.haversine_km(0, 0, 0, 1) == pytest.approx(111.19, abs=0.05)


def test_cercanas_ordena_y_encuentra_la_propia_sede():
    cfe = df[df["siglas"] == "CFE"].iloc[0]
    r = datos.cercanas(df, cfe["lat"], cfe["lon"], 5)
    assert r["distancia_km"].is_monotonic_increasing
    assert r.iloc[0]["siglas"] == "CFE" and r.iloc[0]["distancia_km"] == 0


def test_atipicas_marca_las_lejanas():
    r = datos.con_atipicas(df)
    assert r.loc[r["siglas"].isin(["COPRISEG", "ICATEGRO"]), "atipica"].all()


def test_endpoint_cercanas():
    c = TestClient(app)
    r = c.get("/api/cercanas", params={"lat": 16.8531, "lon": -99.8237, "limite": 3})
    assert r.status_code == 200 and len(r.json()) == 3 and "distancia_km" in r.json()[0]
    assert c.get("/api/cercanas").status_code == 422
