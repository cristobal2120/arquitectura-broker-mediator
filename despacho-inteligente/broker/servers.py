from abc import ABC, abstractmethod
import threading
import logging
import time
from typing import List

logger = logging.getLogger(__name__)


class BaseServer(ABC):
    def __init__(self, nombre: str, topics: List[str], group_id: str):
        self.nombre = nombre
        self.topics = topics
        self.group_id = group_id
        self._running = False

    def iniciar(self, en_hilo: bool = False):
        if en_hilo:
            hilo = threading.Thread(target=self._run, daemon=True, name=self.nombre)
            hilo.start()
        else:
            self._run()

    def _run(self):
        try:
            self._running = True
            logger.info(f"[{self.nombre}] Iniciando server con topics: {self.topics}")
            self.ejecutar()
        except Exception as e:
            logger.error(f"[{self.nombre}] ERROR: {e}", exc_info=True)

    @abstractmethod
    def ejecutar(self):
        pass


# ──────────────────────────────────────────────
# SERVERS SIMULADOS (MEJORADOS)
# ──────────────────────────────────────────────

class EmpresaAServer(BaseServer):
    """Simula sistema SOAP — respuesta lenta de 2s"""

    def __init__(self):
        super().__init__("EmpresaA", ["empresaA-topic"], "empresaA-group")

    def ejecutar(self):
        while True:
            logger.info("[EmpresaA/SOAP] Procesando request SOAP envelope...")
            time.sleep(2)  # latencia SOAP
            logger.info("[EmpresaA/SOAP] Response generado")
            time.sleep(3)


class EmpresaBServer(BaseServer):
    """Simula sistema REST — respuesta rápida"""

    def __init__(self):
        super().__init__("EmpresaB", ["empresaB-topic"], "empresaB-group")

    def ejecutar(self):
        while True:
            logger.info("[EmpresaB/REST] GET /api/inventario procesado")
            time.sleep(4)


class EmpresaCServer(BaseServer):
    """Simula sistema CSV via FTP"""

    def __init__(self):
        super().__init__("EmpresaC", ["empresa_c_requests"], "empresa_c_group")

    def ejecutar(self):
        while True:
            logger.info("[EmpresaC/FTP-CSV] Leyendo archivo envios.csv via FTP...")
            time.sleep(1)  # parseo
            logger.info("[EmpresaC/FTP-CSV] CSV parseado, 3 registros encontrados")
            time.sleep(4)


class DespachoServer(BaseServer):
    def __init__(self):
        super().__init__("Despacho", ["despacho-topic"], "despacho-group")

    def ejecutar(self):
        while True:
            logger.info("[Despacho] Coordinando despacho...")
            time.sleep(5)


class NuevoEnvioServer(BaseServer):
    def __init__(self):
        super().__init__("NuevoEnvio", ["nuevo-envio-topic"], "nuevo-envio-group")

    def ejecutar(self):
        while True:
            logger.info("[NuevoEnvio] Procesando nuevos envíos...")
            time.sleep(5)