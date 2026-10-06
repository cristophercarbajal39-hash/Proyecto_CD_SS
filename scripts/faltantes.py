"""Completa datos de dependencias desde una hoja de cálculo.

    python -m scripts.faltantes generar              # crea data/faltantes.csv (ábrelo en Excel/LibreOffice)
    python -m scripts.faltantes fusionar [--dry-run] # vuelca el CSV a data/dependencias.json

Reglas: celda vacía = no cambia nada. Carreras separadas por ";". Modalidad: Presencial, Híbrida o Remota.
Plazas: número entero. convenio_estado: vigente | no vigente.
"""
import argparse
import csv
import json
from pathlib import Path

from app.datos import CARRERAS, DATA

CSV, JSON = DATA / "faltantes.csv", DATA / "dependencias.json"
TEXTO = ["ubicacion", "area", "modalidad", "plazas", "horario", "requisitos", "duracion", "contacto"]
COLS = ["id", "nombre", "carreras"] + TEXTO + ["convenio_estado", "convenio_vigencia"]
MODALIDADES = {"Presencial", "Híbrida", "Remota"}


def generar(csv_path: Path = CSV, json_path: Path = JSON) -> int:
    deps = json.loads(Path(json_path).read_text(encoding="utf-8"))
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel respeta acentos
        w = csv.DictWriter(f, COLS); w.writeheader()
        for d in deps:
            conv = d.get("convenio") or {}
            fila = {"id": d["id"], "nombre": d["nombre"], "carreras": ";".join(d.get("carreras") or []),
                    "convenio_estado": conv.get("estado", ""), "convenio_vigencia": conv.get("vigencia", "")}
            fila.update({k: d.get(k) if d.get(k) is not None else "" for k in TEXTO})
            w.writerow(fila)
    return len(deps)


def fusionar(csv_path: Path = CSV, json_path: Path = JSON, dry_run: bool = False):
    """Devuelve (campos_cambiados, avisos)."""
    deps = json.loads(Path(json_path).read_text(encoding="utf-8"))
    por_id = {d["id"]: d for d in deps}
    cambios, avisos = 0, []

    def poner(d, clave, valor):
        nonlocal cambios
        if d.get(clave) != valor:
            d[clave] = valor; cambios += 1

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for n, fila in enumerate(csv.DictReader(f), start=2):
            fila = {k: (v or "").strip() for k, v in fila.items()}
            d = por_id.get(int(fila["id"])) if fila["id"].isdigit() else None
            if d is None:
                avisos.append(f"Fila {n}: id '{fila['id']}' no existe."); continue
            for k in TEXTO:
                v = fila.get(k, "")
                if not v:
                    continue
                if k == "modalidad" and v not in MODALIDADES:
                    avisos.append(f"Fila {n} ({d['nombre'][:30]}): modalidad '{v}' no válida."); continue
                if k == "plazas":
                    if not v.isdigit():
                        avisos.append(f"Fila {n}: plazas '{v}' no es un entero."); continue
                    v = int(v)
                poner(d, k, v)
            if fila.get("carreras"):
                lista = [c.strip() for c in fila["carreras"].split(";") if c.strip()]
                for c in [c for c in lista if c not in CARRERAS]:
                    avisos.append(f"Fila {n}: carrera '{c}' no está en el catálogo.")
                poner(d, "carreras", [c for c in lista if c in CARRERAS] or None)
            estado = fila.get("convenio_estado", "").lower()
            if estado and estado not in ("vigente", "no vigente"):
                avisos.append(f"Fila {n}: convenio_estado '{estado}' no válido."); estado = ""
            if estado or fila.get("convenio_vigencia"):
                conv = dict(d.get("convenio") or {})
                if estado: conv["estado"] = estado
                if fila.get("convenio_vigencia"): conv["vigencia"] = fila["convenio_vigencia"]
                poner(d, "convenio", conv)
    if not dry_run:
        Path(json_path).write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
    return cambios, avisos


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["generar", "fusionar"]); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.accion == "generar":
        print(f"{generar()} filas escritas en {CSV}")
    else:
        c, av = fusionar(dry_run=a.dry_run)
        print(f"{c} campos {'por cambiar (dry-run)' if a.dry_run else 'actualizados'}."); [print("AVISO:", x) for x in av]
