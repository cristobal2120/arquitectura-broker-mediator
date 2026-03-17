"""
mediator/coordinador.py

Implementación del patrón MEDIATOR para el módulo de Despacho Inteligente.

Regla fundamental:
  - Ninguna entidad (Camion, Almacen, Seguros) puede conocer a otra.
  - Toda comunicación ocurre a través de IMediator.notify().
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# INTERFAZ MEDIATOR
# ──────────────────────────────────────────────

class IMediator(ABC):
    """
    Contrato que deben cumplir todos los coordinadores.
    Las entidades sólo conocen esta interfaz — nunca la implementación concreta.
    """

    @abstractmethod
    def notify(self, sender: "ComponenteBase", evento: str, datos: dict) -> Optional[dict]:
        """
        Punto central de comunicación.

        :param sender: Objeto que origina el evento.
        :param evento: Nombre del evento (ej. 'camion_listo', 'stock_verificado').
        :param datos:  Payload del evento.
        :return: Respuesta opcional del mediador.
        """


# ──────────────────────────────────────────────
# BASE DE COMPONENTES
# ──────────────────────────────────────────────

class ComponenteBase:
    """
    Clase base para todas las entidades.
    Solo sabe que existe un IMediator — no quién es.
    """

    def __init__(self, nombre: str):
        self.nombre = nombre
        self._mediator: Optional[IMediator] = None

    def set_mediator(self, mediator: IMediator) -> None:
        self._mediator = mediator

    def _emitir(self, evento: str, datos: dict) -> Optional[dict]:
        if self._mediator is None:
            raise RuntimeError(f"{self.nombre}: mediator no configurado.")
        logger.info("[%s] emite evento '%s'", self.nombre, evento)
        return self._mediator.notify(self, evento, datos)


# ──────────────────────────────────────────────
# ENTIDADES DE DOMINIO
# Ninguna importa a ninguna otra. Sólo usan _emitir().
# ──────────────────────────────────────────────

@dataclass
class Camion(ComponenteBase):
    id_camion: str = ""
    estado: str = "disponible"      # disponible | en_ruta | mantenimiento
    carga_actual_kg: float = 0.0
    capacidad_max_kg: float = 5000.0

    def __post_init__(self):
        super().__init__(f"Camion-{self.id_camion}")

    def solicitar_despacho(self, pedido_id: str, peso_kg: float) -> dict:
        """El camión pide al Coordinador que gestione el despacho completo."""
        return self._emitir("camion_solicita_despacho", {
            "pedido_id": pedido_id,
            "camion_id": self.id_camion,
            "peso_kg": peso_kg,
        })

    def confirmar_salida(self, pedido_id: str) -> None:
        self.estado = "en_ruta"
        self._emitir("camion_en_ruta", {"pedido_id": pedido_id, "camion_id": self.id_camion})


@dataclass
class Almacen(ComponenteBase):
    id_almacen: str = ""
    stock: dict = field(default_factory=dict)   # {producto_id: cantidad}

    def __post_init__(self):
        super().__init__(f"Almacen-{self.id_almacen}")

    def verificar_stock(self, producto_id: str, cantidad: int) -> bool:
        disponible = self.stock.get(producto_id, 0) >= cantidad
        self._emitir("stock_verificado", {
            "producto_id": producto_id,
            "cantidad": cantidad,
            "disponible": disponible,
        })
        return disponible

    def reservar_stock(self, producto_id: str, cantidad: int) -> None:
        if producto_id in self.stock:
            self.stock[producto_id] -= cantidad
        self._emitir("stock_reservado", {
            "producto_id": producto_id,
            "cantidad": cantidad,
        })


@dataclass
class Seguros(ComponenteBase):
    id_poliza: str = ""
    vigente: bool = True
    cobertura_max_kg: float = 10000.0

    def __post_init__(self):
        super().__init__("Seguros")

    def validar_poliza(self, camion_id: str, peso_kg: float) -> bool:
        valido = self.vigente and peso_kg <= self.cobertura_max_kg
        self._emitir("poliza_validada", {
            "camion_id": camion_id,
            "peso_kg": peso_kg,
            "aprobado": valido,
        })
        return valido


# ──────────────────────────────────────────────
# COORDINADOR DE DESPACHO — implementa IMediator
# Es el ÚNICO lugar donde existe lógica de coordinación.
# ──────────────────────────────────────────────

class CoordinadorDespacho(IMediator):
    """
    Evita el 'código espagueti':
    Camion no habla con Almacen ni con Seguros.
    Seguros no habla con Camion ni con Almacen.
    Todo pasa por aquí.
    """

    def __init__(self, almacen: Almacen, seguros: Seguros):
        self._almacen = almacen
        self._seguros = seguros
        self._log: list[dict] = []          # auditoría de eventos

        # Registrar este coordinador en cada entidad
        almacen.set_mediator(self)
        seguros.set_mediator(self)

    def registrar_camion(self, camion: Camion) -> None:
        camion.set_mediator(self)

    # ── Punto central de despacho ──────────────────

    def notify(self, sender: ComponenteBase, evento: str, datos: dict) -> Optional[dict]:
        entrada = {"sender": sender.nombre, "evento": evento, "datos": datos}
        self._log.append(entrada)
        logger.info("[Coordinador] recibe '%s' de %s", evento, sender.nombre)

        if evento == "camion_solicita_despacho":
            return self._flujo_despacho(datos)

        if evento == "camion_en_ruta":
            logger.info("[Coordinador] camion %s salió hacia pedido %s",
                        datos["camion_id"], datos["pedido_id"])
            return {"estado": "en_ruta"}

        if evento in ("stock_verificado", "stock_reservado", "poliza_validada"):
            # Eventos informativos — el coordinador los registra, no hace nada más
            return None

        logger.warning("[Coordinador] evento desconocido: '%s'", evento)
        return None

    # ── Flujo orquestado (solo el coordinador conoce el orden) ──

    def _flujo_despacho(self, datos: dict) -> dict:
        pedido_id  = datos["pedido_id"]
        camion_id  = datos["camion_id"]
        peso_kg    = datos["peso_kg"]

        # 1. Verificar stock (el coordinador llama al Almacen, no el Camion)
        producto_id = f"prod-{pedido_id}"
        hay_stock = self._almacen.verificar_stock(producto_id, cantidad=1)
        if not hay_stock:
            return {"ok": False, "razon": "sin_stock", "pedido_id": pedido_id}

        # 2. Validar póliza de seguros (el coordinador llama a Seguros, no el Camion)
        seguro_ok = self._seguros.validar_poliza(camion_id, peso_kg)
        if not seguro_ok:
            return {"ok": False, "razon": "seguro_invalido", "pedido_id": pedido_id}

        # 3. Reservar stock
        self._almacen.reservar_stock(producto_id, cantidad=1)

        logger.info("[Coordinador] despacho APROBADO para pedido %s", pedido_id)
        return {"ok": True, "pedido_id": pedido_id, "camion_id": camion_id}

    def get_log(self) -> list[dict]:
        return list(self._log)


# ──────────────────────────────────────────────
# FACTORY — construye el subsistema completo
# ──────────────────────────────────────────────

def crear_subsistema_despacho() -> tuple[CoordinadorDespacho, list[Camion]]:
    almacen = Almacen(
        id_almacen="A1",
        stock={"prod-PED001": 10, "prod-PED002": 5, "prod-PED003": 0},
    )
    seguros = Seguros(id_poliza="POL-2024", vigente=True, cobertura_max_kg=8000.0)
    coordinador = CoordinadorDespacho(almacen, seguros)

    camiones = [
        Camion(id_camion="C001", capacidad_max_kg=5000),
        Camion(id_camion="C002", capacidad_max_kg=3000),
    ]
    for c in camiones:
        coordinador.registrar_camion(c)

    return coordinador, camiones
