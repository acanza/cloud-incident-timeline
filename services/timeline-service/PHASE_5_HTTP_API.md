# Timeline Service - Phase 5: HTTP API

## Descripción General

La Fase 5 implementa los endpoints HTTP que expone el timeline-service a través del ALB.

## Arquitectura

```
ALB (Application Load Balancer)
  ↓
FastAPI Application (port 80)
  ├─ GET /health
  ├─ GET /incidents/{incident_id}/timeline
  └─ POST /incidents/{incident_id}/timeline/comments

Concurrentemente:
  └─ SQS Consumer (polling loop)
```

## Componentes

### 1. **Health Endpoint** (`src/routes/health.py`)

Endpoint de health check para ALB y monitoreo.

#### `GET /health`

```
Método: GET
Ruta: /health
Autenticación: No
Response: 200 OK

Cuerpo:
{
  "status": "ok",
  "service": "timeline-service"
}
```

**Propósito:**
- ALB usa para health checks (target group)
- Monitoreo: verifica si servicio está vivo
- Kubernetes/ECS: readiness probe

**Ejemplos:**
```bash
curl http://localhost/health
# {"status":"ok","service":"timeline-service"}

curl http://alb.example.com/health
# {"status":"ok","service":"timeline-service"}
```

---

### 2. **Timeline Endpoints** (`src/routes/timeline.py`)

#### `GET /incidents/{incident_id}/timeline`

Obtiene el timeline (historial de eventos) de un incidente.

```
Método: GET
Ruta: /incidents/{incident_id}/timeline
Autenticación: No
Response: 200 OK

Parámetros:
  incident_id (string, path): ID del incidente

Cuerpo:
{
  "incident_id": "inc-001",
  "entries": [
    {
      "incident_id": "inc-001",
      "timeline_entry_id": "tl-001",
      "created_at": "2026-07-30T08:00:00Z",
      "message": "Incident created with HIGH severity and OPEN status.",
      "event_type": "IncidentCreated",
      "source_event_id": "evt-001"
    },
    {
      "incident_id": "inc-001",
      "timeline_entry_id": "tl-002",
      "created_at": "2026-07-30T08:15:00Z",
      "message": "Status changed from OPEN to INVESTIGATING.",
      "event_type": "IncidentStatusChanged",
      "source_event_id": "evt-002"
    }
  ]
}
```

**Detalles:**
- Entries ordenadas cronológicamente (newest first)
- Cada entrada contiene mensaje legible para usuario
- source_event_id usado para deduplicación interno

**Errores:**

```
400 Bad Request
{
  "message": "incident_id must be a non-empty string",
  "error_code": "VALIDATION_ERROR"
}

500 Internal Server Error
{
  "message": "Failed to retrieve timeline",
  "error_code": "INTERNAL_ERROR"
}
```

**Ejemplos:**
```bash
# Obtener timeline de incidente
curl http://alb.example.com/incidents/inc-001/timeline
# → 200 OK with entries

# Incidente sin timeline entries
curl http://alb.example.com/incidents/inc-999/timeline
# → 200 OK with empty entries []

# ID inválido
curl http://alb.example.com/incidents//timeline
# → 400 Bad Request
```

---

#### `POST /incidents/{incident_id}/timeline/comments`

Agrega un comentario manual al timeline (Opcional - Recomendado para portfolio).

```
Método: POST
Ruta: /incidents/{incident_id}/timeline/comments
Autenticación: No
Response: 201 Created

Parámetros:
  incident_id (string, path): ID del incidente

Request Body:
{
  "comment": "Backend team is investigating database metrics",
  "user_id": "user-123"
}

Response:
{
  "timeline_entry_id": "tl-003",
  "incident_id": "inc-001",
  "message": "Comment: Backend team is investigating database metrics",
  "created_at": "2026-07-30T08:40:00Z"
}
```

**Detalles:**
- `comment` requerido, máximo 1000 caracteres
- `user_id` opcional
- Crea una entrada manual de timeline
- Inmediatamente visible en GET /incidents/{id}/timeline

**Errores:**

```
400 Bad Request
{
  "message": "comment is required",
  "error_code": "VALIDATION_ERROR",
  "details": {"field": "comment"}
}

400 Bad Request (si comment > 1000 chars)
{
  "message": "comment cannot exceed 1000 characters",
  "error_code": "VALIDATION_ERROR"
}

500 Internal Server Error
{
  "message": "Failed to add comment",
  "error_code": "INTERNAL_ERROR"
}
```

**Ejemplos:**
```bash
# Agregar comentario
curl -X POST http://alb.example.com/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Database team working on optimization",
    "user_id": "user-456"
  }'
# → 201 Created

# Sin comentario
curl -X POST http://alb.example.com/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-456"}'
# → 400 Bad Request (comment required)
```

---

## Estructura de Aplicación FastAPI

### Main Application (`src/main.py`)

```python
from fastapi import FastAPI

app = create_app()
# ↓ Incluye routers
# ├─ health router
# └─ timeline router
```

**Flujo de Inicialización:**

1. `create_app()` → FastAPI instance
2. Validar configuración (environment variables)
3. Registrar route modules
4. Configurar exception handlers
5. Configurar startup/shutdown events

**Exception Handler Global:**

Convierte `TimelineServiceException` a respuestas HTTP apropiadas:
```python
@app.exception_handler(TimelineServiceException)
async def timeline_exception_handler(request, exc):
    # Mapea error_code a status_code
    # Retorna JSON error response
```

**Eventos:**

```python
@app.on_event("startup")
# Log: "Timeline service starting up"

@app.on_event("shutdown")
# Log: "Timeline service shutting down"
```

---

## Ejecución

### Local (Desarrollo)

```bash
cd services/timeline-service

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export AWS_REGION=us-east-1
export TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline
export TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../timeline-queue

# Ejecutar FastAPI
python -m src.main
# ← Escucha en 0.0.0.0:80

# En otra terminal, ejecutar consumer
python -m src.consumer  # (implementado en Fase 6)
```

### Prod (ECS/Docker)

```bash
# Desde Dockerfile
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 80 & python -m src.consumer"]
```

---

## Routing en ALB

El ALB debe estar configurado con path-based routing:

```
Priority 10: /incidents/*/timeline* → timeline-service target group
Priority 20: /incidents*            → incident-service target group

Health Check:
  Path: /health
  Expected: 200 OK with {"status":"ok"}
```

**Nota:** Si no está configurado, agregarlo manualmente en AWS Console o Terraform.

---

## Conformidad con Especificaciones

✅ **HTTP API Contracts** (Sec. 7.2)

| Endpoint | Status | Especificación |
|----------|--------|----------------|
| GET /health | ✅ Implementado | Health check |
| GET /incidents/{id}/timeline | ✅ Implementado | Query timeline |
| POST /incidents/{id}/timeline/comments | ✅ Implementado | Add comment (opcional) |

✅ **Response Format** (Sec. 7.2)

- JSON response bodies
- Timestamps en ISO format con Z suffix
- Errores en formato consistente
- HTTP status codes correcto

✅ **Error Handling** (Sec. 10)

- Validación de input
- Errores en JSON
- Status codes apropiados

---

## Integration con SQS Consumer

La aplicación FastAPI y el SQS consumer corren **concurrentemente**:

```
Proceso Principal (ECS Task):
  ├─ FastAPI HTTP API (puerto 80)
  │   └─ Escucha requests de ALB
  │
  └─ SQS Consumer (background)
      └─ Poll queue, procesa eventos
```

Ambos comparten:
- Misma configuración (env vars)
- Mismos clientes AWS (DynamoDB, SQS, EventBridge)
- Mismos modelos y servicios

---

## Testing Endpoints

Usar ALB o localhost:

```bash
# Health check
curl http://localhost/health

# Get timeline (vacío al principio)
curl http://localhost/incidents/inc-001/timeline

# Add comment
curl -X POST http://localhost/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"Investigating issue","user_id":"user-1"}'

# Get timeline (ahora con comentario)
curl http://localhost/incidents/inc-001/timeline
```

---

## OpenAPI/Swagger

FastAPI genera documentación automáticamente:

- **Swagger UI:** `GET /docs`
- **ReDoc:** `GET /redoc`

Útil para desarrollo e integración.

---

## Próximas Fases

- **Fase 6**: Dockerization (multi-process orchestration)
- **Fase 7**: Documentation & README

## Notas Importantes

1. **Concurrent Execution**: FastAPI + SQS Consumer corren juntos en mismo proceso
2. **Port**: Escucha en 0.0.0.0:80 (requerido por ALB)
3. **Graceful Shutdown**: Signal handlers en consumer respetan shutdown de ECS
4. **Error Handling**: Excepciones se convierten a HTTP responses automáticamente
5. **Logging**: Todos los endpoints loguean con contexto (incident_id, etc)
6. **Security**: Sin autenticación en MVP (puede agregarse con FastAPI Security)
7. **CORS**: Sin configuración CORS (interno a VPC, no necesario)
