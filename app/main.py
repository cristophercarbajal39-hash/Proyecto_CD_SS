import json
import datetime as dt
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import datos

BASE = Path(__file__).parent
DATA = BASE.parent / "data"
app = FastAPI(title="Servicio Social Tec")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
tpl = Jinja2Templates(directory=BASE / "templates")
MES = "ene feb mar abr may jun jul ago sep oct nov dic".split()


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def rango(it):
    a = dt.date.fromisoformat(it["inicio"])
    b = dt.date.fromisoformat(it["fin"])
    if a == b:
        return f"{a.day} {MES[a.month-1]} {a.year}"
    return f"{a.day} {MES[a.month-1]} – {b.day} {MES[b.month-1]} {b.year}"


tpl.env.filters["rango"] = rango

FAQ = [
    ("¿Qué es el servicio social?", "Actividad obligatoria que realizas en una dependencia para liberar tu carrera. (Texto por confirmar con Vinculación.)"),
    ("¿Cuánto dura?", "El periodo vigente va del 3 de noviembre de 2026 al 25 de mayo de 2027, con tres reportes y uno final. Las horas requeridas: por confirmar."),
    ("¿Qué documentos necesito?", "Solicitud de ingreso, carta compromiso, carta de presentación, carta de aceptación, plan de trabajo, reportes y carta de terminación. Consulta el Proceso."),
    ("¿Cómo sé qué dependencias aceptan mi carrera?", "Usa Buscar dependencias y filtra por carrera."),
    ("¿Puedo hacer mi servicio social fuera del Tec?", "Por confirmar con Vinculación."),
    ("¿Cómo sé si una dependencia tiene convenio vigente?", "Revisa la sección Convenios."),
    ("¿Qué pasa si una dependencia no aparece en el sistema?", "Por confirmar con Vinculación."),
    ("¿Dónde entrego mis documentos?", "En la oficina de servicio social del Depto. de Gestión Tecnológica y Vinculación."),
]
AYUDA = [
    ("Cómo buscar una dependencia", "Escribe el nombre o el área en la barra de búsqueda de Buscar dependencias."),
    ("Cómo utilizar los filtros", "Elige tu carrera y el resultado se actualiza al instante."),
    ("Cómo consultar el mapa", "Pulsa «Usar mi ubicación» o haz clic en el mapa para marcar tu casa."),
    ("Cómo revisar los convenios", "En Convenios verás el estado de cada institución."),
    ("Qué hacer si la información está desactualizada", "Escribe a vin_acapulco@tecnm.mx."),
]


def view(req: Request, name: str, **ctx):
    return tpl.TemplateResponse(req, name, {"active": req.url.path, **ctx})


def roadmap(hoy: dt.date):
    etapas = load("calendario.json")["etapas"]
    h = hoy.isoformat()
    for e in etapas:
        ini = min(i["inicio"] for i in e["items"])
        fin = max(i["fin"] for i in e["items"])
        e["estado"] = "hecho" if fin < h else ("actual" if ini <= h else "pendiente")
    todos = [i for e in etapas for i in e["items"] if i["fin"] >= h]
    prox = min(todos, key=lambda i: i["fin"]) if todos else None
    dias = (dt.date.fromisoformat(prox["fin"]) - hoy).days if prox else None
    return etapas, prox, dias


@app.get("/")
def inicio(req: Request):
    return view(req, "index.html")


@app.get("/dependencias")
def dependencias(req: Request):
    return view(req, "dependencias.html", deps=load("dependencias.json"), buscar=False)


@app.get("/buscar")
def buscar(req: Request):
    return view(req, "dependencias.html", deps=load("dependencias.json"), buscar=True)


@app.get("/proceso")
def proceso(req: Request):
    etapas, prox, dias = roadmap(dt.date.today())
    return view(req, "proceso.html", etapas=etapas, prox=prox, dias=dias, cal=load("calendario.json"))


@app.get("/mapa")
def mapa(req: Request):
    return view(req, "mapa.html")


@app.get("/convenios")
def convenios(req: Request):
    return view(req, "convenios.html", deps=load("dependencias.json"))


@app.get("/preguntas")
def preguntas(req: Request):
    return view(req, "info.html", titulo="Preguntas frecuentes", lead="Resuelve tus dudas sobre el servicio social.", items=FAQ)


@app.get("/ayuda")
def ayuda(req: Request):
    return view(req, "info.html", titulo="¿Cómo podemos ayudarte?", lead="Guía rápida para usar la plataforma.", items=AYUDA)


@app.get("/proposito")
def proposito(req: Request):
    return view(req, "info.html", titulo="Nuestro propósito",
                lead="Facilitar a los estudiantes la búsqueda de instituciones donde puedan realizar su servicio social, con información organizada sobre dependencias, requisitos, ubicación, convenios y áreas disponibles.",
                items=[("¿Qué problema resolvemos?", "Muchos estudiantes no saben qué dependencias aceptan su carrera, dónde están, qué requisitos piden o si tienen convenio. Esta plataforma reúne esa información en un solo lugar.")])


@app.get("/api/dependencias")
def api_dependencias():
    return load("dependencias.json")


@app.get("/api/calendario")
def api_calendario():
    return load("calendario.json")


@app.get("/api/cercanas")
def api_cercanas(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                 limite: int = Query(10, ge=1, le=50)):
    """Sedes más cercanas a (lat, lon), en línea recta."""
    df = datos.cercanas(datos.cargar_dependencias(), lat, lon, limite)
    return datos.a_registros(df[["id", "nombre", "sede", "etiqueta", "lat", "lon", "distancia_km"]])
