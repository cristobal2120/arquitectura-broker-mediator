from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import uuid
import threading
import time

app = FastAPI(title="Portal Despacho Inteligente")

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# MODELOS
# ──────────────────────────────────────────────

class ConsultaRequest(BaseModel):
    sku: str


class DespachoRequest(BaseModel):
    pedido_id: str
    camion_id: str
    peso_kg: float


class NuevoEnvioRequest(BaseModel):
    ciudad_destino: str
    peso_kg: float


# 🔥 NUEVO MODELO (Empresa C)
class ConsultaCSVRequest(BaseModel):
    numero_guia: str


# ──────────────────────────────────────────────
# ALMACÉN DE RESPUESTAS
# ──────────────────────────────────────────────

_respuestas: Dict[str, dict] = {}


# ──────────────────────────────────────────────
# FUNCIONES SIMULADAS
# ──────────────────────────────────────────────

def procesar_empresa_a(cid: str):
    time.sleep(2)
    _respuestas[cid] = {
        "estado": "listo",
        "respuesta": "Stock disponible en Empresa A"
    }


def procesar_despacho(cid: str, data: DespachoRequest):
    time.sleep(1)

    if data.peso_kg > 8000:
        resultado = "RECHAZADO: Peso excede cobertura"
    elif data.pedido_id == "PED002":
        resultado = "RECHAZADO: Sin stock"
    else:
        resultado = "APROBADO"

    _respuestas[cid] = {
        "estado": "listo",
        "respuesta": resultado
    }


def procesar_nuevo_envio(cid: str):
    time.sleep(1.5)
    _respuestas[cid] = {
        "estado": "listo",
        "respuesta": "Envío registrado correctamente"
    }


# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/")
def root():
    return {"mensaje": "Portal activo 🚀"}


@app.post("/consulta/empresa-a")
def consulta_empresa_a(req: ConsultaRequest):
    cid = str(uuid.uuid4())

    _respuestas[cid] = {"estado": "procesando"}

    threading.Thread(
        target=procesar_empresa_a,
        args=(cid,),
        daemon=True
    ).start()

    return {"correlation_id": cid}


# 🔥 NUEVO ENDPOINT EMPRESA C (CSV)
@app.post("/consulta/empresa-c")
def consulta_empresa_c(req: ConsultaCSVRequest):
    cid = str(uuid.uuid4())

    _respuestas[cid] = {"estado": "procesando"}

    threading.Thread(
        target=lambda: (
            time.sleep(1),
            _respuestas.update({
                cid: {
                    "estado": "listo",
                    "respuesta": f"Guía {req.numero_guia} encontrada en CSV — Ciudad: Bogotá, Peso: 15kg"
                }
            })
        ),
        daemon=True
    ).start()

    return {"correlation_id": cid}


@app.post("/despacho")
def despacho(req: DespachoRequest):
    cid = str(uuid.uuid4())

    _respuestas[cid] = {"estado": "procesando"}

    threading.Thread(
        target=procesar_despacho,
        args=(cid, req),
        daemon=True
    ).start()

    return {"correlation_id": cid}


@app.post("/nuevo-envio")
def nuevo_envio(req: NuevoEnvioRequest):
    cid = str(uuid.uuid4())

    _respuestas[cid] = {"estado": "procesando"}

    threading.Thread(
        target=procesar_nuevo_envio,
        args=(cid,),
        daemon=True
    ).start()

    return {"correlation_id": cid}


@app.get("/respuesta/{cid}")
def obtener_respuesta(cid: str):
    return _respuestas.get(cid, {"estado": "no_encontrado"})