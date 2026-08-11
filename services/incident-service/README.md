# Incident Service

HTTP API para la gestión de incidentes. Maneja el ciclo de vida y estado actual de los incidentes.

## Stack Técnico

- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **AWS SDK**: boto3
- **Base de datos**: DynamoDB
- **Event Bus**: EventBridge
- **Logging**: JSON estructurado

## Estructura de Directorios

```
incident-service/
├── src/
│   ├── main.py              # Punto de entrada de FastAPI
│   ├── config.py            # Configuración desde variables de entorno
│   ├── constants.py         # Constantes y enumeraciones compartidas
│   ├── schemas.py           # Modelos Pydantic para requests/responses
│   ├── logger.py            # Configuración de logging estructurado
│   ├── context.py           # Manejo de Correlation ID
│   ├── utils.py             # Utilidades y validaciones
│   ├── services/            # Lógica de negocio (próxima fase)
│   ├── handlers/            # Handlers de endpoints (próxima fase)
│   └── models/              # Modelos de datos (próxima fase)
├── Dockerfile               # Imagen Docker
├── .dockerignore            # Archivos a ignorar en build
├── requirements.txt         # Dependencias Python
├── .env.example             # Variables de entorno de ejemplo
└── README.md                # Esta documentación
```

## Variables de Entorno

**Requeridas:**

```bash
AWS_REGION=eu-west-3
INCIDENTS_TABLE_NAME=cloud-incident-timeline-dev-incidents
EVENT_BUS_NAME=cloud-incident-timeline-dev-event-bus
```

**Opcionales:**

```bash
SERVICE_NAME=incident-service
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
HOST=0.0.0.0
PORT=8001
```

Ver `.env.example` para una plantilla completa.

## Desarrollo Local

### Requisitos

- Python 3.11+
- pip o poetry

### Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar localmente

```bash
# Modo desarrollo (con auto-reload)
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Modo producción
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

Acceder a: `http://localhost:8001`

Documentación interactiva: `http://localhost:8001/docs`

### Health check

```bash
curl http://localhost:8001/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "service": "incident-service"
}
```

## Docker

### Build

```bash
docker build -t incident-service:dev .
```

### Run

```bash
docker run -p 8001:8001 \
  -e AWS_REGION=eu-west-3 \
  -e INCIDENTS_TABLE_NAME=cloud-incident-timeline-dev-incidents \
  -e EVENT_BUS_NAME=cloud-incident-timeline-dev-event-bus \
  incident-service:dev
```

## Convenciones Implementadas (Fase 1)

### ✅ Envelope de Eventos

Todos los eventos publicados a EventBridge siguen esta estructura:

```json
{
  "version": "1.0",
  "event_id": "evt-001",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:00:00Z",
  "correlation_id": "corr-001",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {}
}
```

### ✅ Correlation ID

- Generado automáticamente por middleware si no viene en headers
- Se busca en header `X-Correlation-ID`
- Se incluye en respuestas
- Se registra en todos los logs

### ✅ Logging Estructurado

Todos los logs se emiten en formato JSON con campos:

```json
{
  "timestamp": "2026-07-30T08:00:00Z",
  "level": "INFO",
  "service": "incident-service",
  "message": "Incident created",
  "correlation_id": "corr-001",
  "incident_id": "inc-001"
}
```

### ✅ Respuestas de Error

Formato estándar para errores:

```json
{
  "message": "Validation error",
  "details": [
    {
      "field": "severity",
      "message": "Must be one of: LOW, MEDIUM, HIGH, CRITICAL"
    }
  ]
}
```

### ✅ Validaciones

Estados válidos:
- `OPEN`
- `INVESTIGATING`
- `RESOLVED`
- `CLOSED`

Severidades válidas:
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Testing

```bash
# Ejecutar tests
python -m pytest

# Con cobertura
python -m pytest --cov=src
```

## Siguientes Fases

- **Fase 2**: Implementar endpoints HTTP
- **Fase 3**: Integración con DynamoDB
- **Fase 4**: Publicación a EventBridge
- **Fase 5**: Verificación E2E

## Referencias

- [Especificaciones de servicio](../services-implementation-specs.md)
- [Guía de implementación de servicios](../.instructions.md)
- [Instrucciones globales](../../.github/copilot-instructions.md)
