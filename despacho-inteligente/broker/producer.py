"""
broker/producer.py

Puente (Bridge) entre el Portal de Clientes y el Kafka Message Broker.

Responsabilidad:
  - Serializar solicitudes del portal y publicarlas en el topic correcto.
  - NO espera la respuesta (no bloquea al portal).
  - El correlation_id permite emparejar luego la respuesta asíncrona.
"""

import json
import uuid
import logging
from confluent_kafka import Producer

from config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_EMPRESA_A,
    TOPIC_EMPRESA_B,
    TOPIC_DESPACHO,
    TOPIC_NUEVO_ENVIO,
)

logger = logging.getLogger(__name__)


class PortalBridge:
    """
    Implementa el rol BRIDGE / PROXY del patrón Broker.
    El portal sólo conoce esta clase — nunca los servers directamente.
    """

    def __init__(self):
        self._producer = Producer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "acks": "all",          # confirmación de escritura durable
            "retries": 3,
        })
        logger.info("[Bridge] Conectado a Kafka en %s", KAFKA_BOOTSTRAP_SERVERS)

    # ── API pública del Bridge ────────────────────────────────

    def consultar_empresa_a(self, payload: dict) -> str:
        """
        Publica una solicitud para Empresa A.
        Empresa A tarda 2 s — el portal no se bloquea gracias a Kafka.
        Retorna correlation_id para que el portal consulte la respuesta luego.
        """
        return self._publicar(TOPIC_EMPRESA_A, payload)

    def consultar_empresa_b(self, payload: dict) -> str:
        return self._publicar(TOPIC_EMPRESA_B, payload)

    def solicitar_despacho(self, payload: dict) -> str:
        return self._publicar(TOPIC_DESPACHO, payload)

    def solicitar_nuevo_envio(self, payload: dict) -> str:
        """
        DEMO — añadir un cuarto servidor sin modificar el Client ni el Broker.
        Solo se suscribe a TOPIC_NUEVO_ENVIO.
        """
        return self._publicar(TOPIC_NUEVO_ENVIO, payload)

    # ── Interno ──────────────────────────────────────────────

    def _publicar(self, topic: str, payload: dict) -> str:
        correlation_id = str(uuid.uuid4())
        mensaje = {**payload, "correlation_id": correlation_id}
        self._producer.produce(
            topic,
            key=correlation_id.encode(),
            value=json.dumps(mensaje).encode(),
            on_delivery=self._on_delivery,
        )
        self._producer.flush()
        logger.info("[Bridge] Mensaje publicado → topic=%s | cid=%s", topic, correlation_id)
        return correlation_id

    @staticmethod
    def _on_delivery(err, msg):
        if err:
            logger.error("[Bridge] Error entregando mensaje: %s", err)
        else:
            logger.debug("[Bridge] Confirmado offset=%s topic=%s", msg.offset(), msg.topic())
