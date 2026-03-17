import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s — %(message)s",
)

import uvicorn
from broker.servers import (
    EmpresaAServer,
    EmpresaBServer,
    DespachoServer,
    NuevoEnvioServer,
)

logger = logging.getLogger(__name__)


def main():
    print("🔥 ARRANCANDO MAIN...")  # DEBUG

    logger.info("=" * 60)
    logger.info("  DESPACHO INTELIGENTE — Broker + Mediator")
    logger.info("=" * 60)

    # ── Iniciar todos los servers ──────────────────────────────
    servers = [
        EmpresaAServer(),
        EmpresaBServer(),
        DespachoServer(),
        NuevoEnvioServer(),
    ]

    for srv in servers:
        try:
            srv.iniciar(en_hilo=True)
            logger.info("Server '%s' iniciado en hilo background.", srv.nombre)
        except Exception as e:
            logger.error(f"Error iniciando {srv.nombre}: {e}", exc_info=True)

    # Dar tiempo a que los consumers se registren
    time.sleep(2)

    logger.info("-" * 60)
    logger.info("Portal disponible en http://localhost:8000")
    logger.info("Docs Swagger en  http://localhost:8000/docs")
    logger.info("-" * 60)

    # ── Iniciar portal FastAPI ────────────────────────────────
    try:
        uvicorn.run(
            "portal.api:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )
    except Exception as e:
        logger.error(f"Error levantando FastAPI: {e}", exc_info=True)


if __name__ == "__main__":
    main()