"""
demo_escalabilidad.py

Script de demostración para la presentación en vivo.

Muestra cómo añadir NuevoEnvioServer (cuarto servidor ficticio)
sin modificar ni una línea del portal de clientes.

Requisito: Kafka corriendo (docker-compose up -d)
"""

import time
import logging
import threading
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
PAUSE = 0.5


def separador(titulo: str):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def demo_asincronismo_empresa_a():
    separador("DEMO 1 — Empresa A (2s delay) no bloquea el portal")
    t0 = time.time()
    r = httpx.post(f"{BASE_URL}/consulta/empresa-a", json={"sku": "SKU-001"})
    t1 = time.time()
    data = r.json()
    cid = data["correlation_id"]
    print(f"  ✓ Portal respondió en {(t1-t0)*1000:.0f} ms (no esperó los 2 s de Empresa A)")
    print(f"  correlation_id: {cid}")

    print("  Esperando respuesta asíncrona de Empresa A...")
    for _ in range(10):
        time.sleep(0.5)
        resp = httpx.get(f"{BASE_URL}/respuesta/{cid}").json()
        if resp["estado"] == "listo":
            print(f"  ✓ Respuesta recibida: {resp['respuesta']}")
            return
    print("  ✗ Timeout esperando respuesta (¿están los servers corriendo?)")


def demo_mediator_despacho():
    separador("DEMO 2 — Mediator coordina Camion/Almacen/Seguros")
    casos = [
        ("PED001", "C001", 500, "Stock disponible, seguro válido → APROBADO"),
        ("PED002", "C001", 100, "Sin stock → RECHAZADO"),
        ("PED001", "C001", 9000, "Peso excede cobertura → RECHAZADO"),
    ]
    for pedido, camion, peso, descripcion in casos:
        print(f"\n  Caso: {descripcion}")
        r = httpx.post(f"{BASE_URL}/despacho", json={
            "pedido_id": pedido, "camion_id": camion, "peso_kg": peso
        })
        cid = r.json()["correlation_id"]
        for _ in range(8):
            time.sleep(0.4)
            resp = httpx.get(f"{BASE_URL}/respuesta/{cid}").json()
            if resp["estado"] == "listo":
                print(f"  → {resp['respuesta']}")
                break


def demo_escalabilidad_nuevo_server():
    separador("DEMO 3 — Nuevo servidor añadido sin modificar el portal")
    print("  El portal nunca supo que NuevoEnvioServer existía.")
    print("  Solo llamamos a POST /nuevo-envio — el portal lo rutea al broker.")
    r = httpx.post(f"{BASE_URL}/nuevo-envio", json={
        "ciudad_destino": "Medellín", "peso_kg": 12.5
    })
    cid = r.json()["correlation_id"]
    print(f"  correlation_id: {cid}")
    for _ in range(8):
        time.sleep(0.4)
        resp = httpx.get(f"{BASE_URL}/respuesta/{cid}").json()
        if resp["estado"] == "listo":
            print(f"  ✓ Respuesta de NuevoEnvioServer: {resp['respuesta']}")
            return
    print("  ✗ Sin respuesta (¿está NuevoEnvioServer corriendo?)")


if __name__ == "__main__":
    print("\nVerificando que el portal esté disponible...")
    try:
        httpx.get(f"{BASE_URL}/").raise_for_status()
    except Exception:
        print("ERROR: El portal no responde. Ejecuta 'python main.py' primero.")
        raise SystemExit(1)

    demo_asincronismo_empresa_a()
    time.sleep(1)
    demo_mediator_despacho()
    time.sleep(1)
    demo_escalabilidad_nuevo_server()

    separador("FIN DE LA DEMO")
