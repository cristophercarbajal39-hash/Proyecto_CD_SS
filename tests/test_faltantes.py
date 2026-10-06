import json
import shutil

from app.datos import DATA
from scripts import faltantes


def test_generar_y_fusionar(tmp_path):
    j, c = tmp_path / "d.json", tmp_path / "f.csv"
    shutil.copy(DATA / "dependencias.json", j)
    assert faltantes.generar(c, j) == 30
    c.write_text(c.read_text(encoding="utf-8-sig").replace("1,Comisión Federal de Electricidad,,,,,,,,,,,",
        "1,Comisión Federal de Electricidad,Ing. Sistemas Computacionales;Fantasía,Acapulco,TI,Presencial,3,,,,,vigente,2024-2027"),
        encoding="utf-8-sig")
    cambios, avisos = faltantes.fusionar(c, j)
    d = json.loads(j.read_text(encoding="utf-8"))[0]
    assert cambios == 6 and d["carreras"] == ["Ing. Sistemas Computacionales"] and d["plazas"] == 3
    assert d["convenio"] == {"estado": "vigente", "vigencia": "2024-2027"}
    assert len(avisos) == 1 and "Fantasía" in avisos[0]
