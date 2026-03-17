# Despacho Inteligente — Broker + Mediator

Prototipo funcional que implementa los patrones de diseño **Broker** y **Mediator** usando **Python 3.11** y **Apache Kafka**.

---

## Arquitectura

### Patrón Broker (Middleware Kafka)

```
Portal (Client)
    └─→ PortalBridge (Bridge)
            └─→ Kafka Topics (Broker)
                    ├─→ EmpresaAServer   [empresa_a_requests]  ← 2s delay
                    ├─→ EmpresaBServer   [empresa_b_requests]
                    ├─→ DespachoServer   [despacho_requests]   ← usa Mediator
                    └─→ NuevoEnvioServer [nuevo_envio_requests] ← 4to server
```

**¿Por qué Kafka ayuda a la escalabilidad?**
- Añadir un nuevo server = crear una clase y suscribirse a un topic. Sin tocar el Client.
- El portal nunca se bloquea aunque Empresa A tarde 2 s.
- Si un server cae, los mensajes se conservan en Kafka hasta que vuelva.

### Patrón Mediator (Módulo de Despacho)

```
Camion ──→ IMediator.notify() ──→ CoordinadorDespacho ──→ Almacen
                                                       └─→ Seguros
```

**Regla cumplida:** Ninguna clase de entidad conoce a otra.
- `Camion` no importa `Almacen` ni `Seguros`.
- `Almacen` no importa `Camion` ni `Seguros`.
- `Seguros` no importa `Camion` ni `Almacen`.
- **Toda** coordinación ocurre en `CoordinadorDespacho.notify()`.

**¿Por qué el Mediator ayuda a la mantenibilidad?**
- Para cambiar la lógica de despacho, solo se toca `CoordinadorDespacho`.
- Las entidades pueden probarse unitariamente en aislamiento.
- No hay código espagueti: el flujo completo se lee en `_flujo_despacho()`.

---

## Estructura del proyecto

```
despacho-inteligente/
├── main.py                    # Punto de entrada — levanta servers + portal
├── demo_escalabilidad.py      # Script de demo para presentación
├── requirements.txt
├── docker-compose.yml         # Kafka + Zookeeper + Kafka UI
├── config/
│   └── settings.py            # Topics, group IDs, configuración
├── broker/
│   ├── producer.py            # PortalBridge — publica mensajes en Kafka
│   └── servers.py             # EmpresaA/B/Despacho/NuevoEnvio servers
├── mediator/
│   └── coordinador.py         # IMediator, ComponenteBase, entidades, Coordinador
├── portal/
│   └── api.py                 # FastAPI — endpoints del portal de clientes
└── tests/
    └── test_mediator.py       # Pruebas unitarias del Mediator
```

---

## Instalación y ejecución

### 1. Requisitos
- Docker y Docker Compose
- Python 3.11+

### 2. Levantar Kafka

```bash
docker-compose up -d
```

Verifica que Kafka esté listo:
```bash
docker-compose logs kafka | grep "started"
```

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Ejecutar el sistema completo

```bash
python main.py
```

Esto levanta en un solo proceso:
- `EmpresaAServer` (hilo background)
- `EmpresaBServer` (hilo background)
- `DespachoServer` (hilo background)
- `NuevoEnvioServer` (hilo background)
- Portal FastAPI en `http://localhost:8000`

### 5. Ejecutar la demo

En otra terminal:
```bash
python demo_escalabilidad.py
```

### 6. Ejecutar pruebas

```bash
pytest tests/ -v
```

---

## Endpoints del portal

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/consulta/empresa-a` | Consulta catálogo (async, 2s delay) |
| POST | `/consulta/empresa-b` | Consulta inventario |
| POST | `/despacho` | Solicitar despacho (Mediator) |
| POST | `/nuevo-envio` | Demo cuarto servidor |
| GET | `/respuesta/{cid}` | Obtener respuesta asíncrona |

Documentación interactiva: `http://localhost:8000/docs`  
Kafka UI: `http://localhost:8080`

---

## Flujo de la demo en vivo

### Demo 1 — Asincronismo (Empresa A tarda 2 s)
```bash
# El portal responde en <50ms, no en 2000ms
curl -X POST http://localhost:8000/consulta/empresa-a \
     -H "Content-Type: application/json" \
     -d '{"sku": "SKU-001"}'
# → {"correlation_id": "uuid...", "instruccion": "GET /respuesta/uuid..."}

# Consultar la respuesta (disponible ~2s después)
curl http://localhost:8000/respuesta/<correlation_id>
```

### Demo 2 — Mediator (despacho coordinado)
```bash
curl -X POST http://localhost:8000/despacho \
     -H "Content-Type: application/json" \
     -d '{"pedido_id": "PED001", "camion_id": "C001", "peso_kg": 500}'
```

### Demo 3 — Escalabilidad (cuarto server)
```bash
# NuevoEnvioServer fue añadido sin modificar portal/api.py ni broker/producer.py
# (Solo se creó la clase y se registró en main.py)
curl -X POST http://localhost:8000/nuevo-envio \
     -H "Content-Type: application/json" \
     -d '{"ciudad_destino": "Medellín", "peso_kg": 12.5}'
```

---

## Diagrama de clases resumido

**Broker:**
```
Client          Bridge          Broker        Servers
Portal ──────→ PortalBridge ──→ Kafka ──────→ EmpresaAServer
                                         ├──→ EmpresaBServer
                                         ├──→ DespachoServer
                                         └──→ NuevoEnvioServer  ← nuevo sin tocar Client
```

**Mediator:**
```
IMediator
    └─ CoordinadorDespacho
            ├─ conoce: Almacen
            ├─ conoce: Seguros
            └─ conoce: Camion[]
Camion ──→ IMediator.notify()  (NO conoce Almacen ni Seguros)
Almacen ──→ IMediator.notify() (NO conoce Camion ni Seguros)
Seguros ──→ IMediator.notify() (NO conoce Camion ni Almacen)
```
