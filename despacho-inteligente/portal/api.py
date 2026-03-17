from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import uuid
import threading
import time

app = FastAPI(title="Portal Despacho Inteligente")

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


# ──────────────────────────────────────────────
# ALMACÉN DE RESPUESTAS (SIMULADO)
# ──────────────────────────────────────────────

_respuestas: Dict[str, dict] = {}


# ──────────────────────────────────────────────
# FUNCIONES SIMULADAS (ASYNC FAKE)
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