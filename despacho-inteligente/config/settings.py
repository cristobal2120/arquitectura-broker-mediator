"""
config/settings.py
Configuración centralizada del sistema.
"""

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Topics del Broker
TOPIC_EMPRESA_A   = "empresa_a_requests"   # consultas al sistema de Empresa A (2s delay)
TOPIC_EMPRESA_B   = "empresa_b_requests"
TOPIC_EMPRESA_C = "empresa_c_requests"
TOPIC_DESPACHO    = "despacho_requests"    # solicitudes de despacho (pasa por Mediator)
TOPIC_NUEVO_ENVIO = "nuevo_envio_requests" # Reto: cuarto servidor sin modificar el Client
TOPIC_RESPONSES   = "portal_responses"    # respuestas hacia el portal (async)

# Group IDs de consumidores
GROUP_EMPRESA_A   = "server-empresa-a"
GROUP_EMPRESA_B   = "server-empresa-b"
GROUP_EMPRESA_C = "server-empresa-c"
GROUP_DESPACHO    = "server-despacho"
GROUP_NUEVO_ENVIO = "server-nuevo-envio"
GROUP_PORTAL      = "portal-response-listener"

# Delay simulado de Empresa A (ms)
EMPRESA_A_DELAY_MS = 2000
