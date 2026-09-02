# Timeline Service - Phase 2: Modelos y Esquemas

## Descripción General

La Fase 2 establece la capa de datos y validación, definiendo todos los modelos necesarios para procesar eventos y persistir entradas de timeline en DynamoDB.

## Estructura de Archivos

```
src/
├── models/
│   ├── __init__.py          # Exportaciones de modelos
│   ├── timeline.py          # Modelo TimelineEntry (DynamoDB)
│   ├── event.py             # Modelos de eventos del dominio
│   ├── validators.py        # Validadores de eventos y timeline
│   └── transformer.py       # Transformadores de eventos a mensajes
├── exceptions.py            # Excepciones personalizadas
├── http_responses.py        # Utilidades HTTP
├── schemas.py              # Esquemas Pydantic adicionales
└── utils.py                # Funciones auxiliares

tests/
└── test_phase2.py          # Tests unitarios
```

## Componentes Implementados

### 1. **TimelineEntry** (`models/timeline.py`)

Modelo de entrada de timeline con métodos de conversión para DynamoDB:

```python
entry = TimelineEntry(
    incident_id="inc-001",
    timeline_entry_id="tl-001",
    created_at="2026-07-30T08:00:00Z",
    message="Incident created with HIGH severity",
    event_type="IncidentCreated",
    source_event_id="evt-001"
)

# Convertir a formato DynamoDB
dynamo_item = entry.to_dynamodb_item()

# Crear desde DynamoDB
entry = TimelineEntry.from_dynamodb_item(dynamo_item)
```

**Estructura DynamoDB:**
- PK: `incident_id`
- SK: `created_at#timeline_entry_id`

### 2. **Modelos de Eventos** (`models/event.py`)

Modelos Pydantic tipados para cada evento del dominio:

- `IncidentCreatedEvent` - Nuevo incidente creado
- `IncidentStatusChangedEvent` - Estado del incidente cambió
- `IncidentSeverityChangedEvent` - Severidad del incidente cambió
- `IncidentResolvedEvent` - Incidente resuelto
- `TimelineCommentAddedEvent` - Comentario agregado al timeline

Cada evento sigue la estructura de sobre estándar:

```json
{
  "version": "1.0",
  "event_id": "evt-001",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:00:00Z",
  "correlation_id": "corr-001",
  "actor": { "user_id": "...", "email": "..." },
  "data": { ... }
}
```

### 3. **Validadores** (`models/validators.py`)

#### `EventValidator`

Valida eventos de SQS/EventBridge:

```python
# Validar estructura cruda
is_valid, error = EventValidator.validate_raw_event(raw_event)

# Verificar si es consumible
if EventValidator.is_consumable_event("IncidentCreated"):
    # Parsear evento tipado
    event = EventValidator.parse_event(raw_event)
```

#### `TimelineEntryValidator`

Valida entradas de timeline:

```python
# Validar entrada
is_valid, error = TimelineEntryValidator.validate_timeline_entry(entry_dict)

# Validar clave de idempotencia
is_valid, error = TimelineEntryValidator.validate_idempotency_key(source_event_id)
```

### 4. **Transformador de Eventos** (`models/transformer.py`)

Convierte eventos de dominio en mensajes legibles para el usuario:

```python
event = IncidentCreatedEvent(...)
message = EventTransformer.transform_incident_created(event)
# "Incident created with HIGH severity and OPEN status."

event = IncidentStatusChangedEvent(...)
message = EventTransformer.transform_status_changed(event)
# "Status changed from OPEN to INVESTIGATING."

event = IncidentResolvedEvent(...)
message = EventTransformer.transform_incident_resolved(event)
# "Incident resolved. Resolution: Database indexes were optimized."
```

**Transformaciones soportadas:**

| Evento | Mensaje Ejemplo |
|--------|-----------------|
| IncidentCreated | "Incident created with HIGH severity and OPEN status." |
| IncidentStatusChanged | "Status changed from OPEN to INVESTIGATING." |
| IncidentSeverityChanged | "Severity changed from MEDIUM to HIGH." |
| IncidentResolved | "Incident resolved. Resolution: ..." |
| TimelineCommentAdded | "Comment: ..." |

### 5. **Excepciones Personalizadas** (`exceptions.py`)

Jerarquía de excepciones para manejo de errores consistente:

```python
try:
    # operación
except ValidationError as e:
    http_exc = handle_service_exception(e)  # → 400 Bad Request

except EventProcessingError as e:
    http_exc = handle_service_exception(e)  # → 500 Internal Error

except ResourceNotFoundError as e:
    http_exc = handle_service_exception(e)  # → 404 Not Found

except IdempotencyError as e:
    http_exc = handle_service_exception(e)  # → 409 Conflict
```

### 6. **Respuestas HTTP** (`http_responses.py`)

Utilidades para respuestas HTTP consistentes:

```python
# Error
raise error_response(400, "Invalid input", "VALIDATION_ERROR", {"field": "..."})

# Manejo de excepciones
try:
    ...
except TimelineServiceException as e:
    raise handle_service_exception(e)

# Respuesta exitosa
return success_response({"incident_id": "inc-001"}, "Created successfully")
```

## Tests Unitarios

Ejecutar tests de Fase 2:

```bash
cd services/timeline-service
pytest tests/test_phase2.py -v
```

**Cobertura de Tests:**

- ✅ Creación y conversión de TimelineEntry
- ✅ Validación de eventos crudos
- ✅ Parsing de eventos tipados
- ✅ Validación de entradas de timeline
- ✅ Transformación de eventos a mensajes
- ✅ Validación de claves de idempotencia

## Validación de Conformidad

La Fase 2 cumple con las siguientes especificaciones:

✅ **Event Contracts** (Sección 4 de specs)
- Estructura de sobre estándar
- Campos requeridos presentes
- Tipado con Pydantic

✅ **Domain Events** (Sección 5 de specs)
- 5 tipos de eventos soportados
- Estructura de datos correcta para cada evento

✅ **Data Models** (Sección 6 de specs)
- Timeline table con PK e SK correctos
- Campos recomendados presentes
- Métodos de conversión DynamoDB

✅ **Event Consumer Behavior** (Sección 8 de specs)
- Transformación correcta de eventos a timeline
- Reglas de transformación implementadas

✅ **Idempotency** (Sección 9 de specs)
- Validación de source_event_id
- Estructura para deduplicación

✅ **Error Handling** (Sección 10 de specs)
- Excepciones personalizadas
- Respuestas JSON consistentes

## Próximas Fases

- **Fase 3**: Capa de acceso a DynamoDB
- **Fase 4**: Procesador de eventos (consumo de SQS)
- **Fase 5**: Consumer SQS
- **Fase 6**: API HTTP

## Notas de Implementación

1. **Idempotencia**: Usar `source_event_id` como clave primaria de deduplicación
2. **Transformaciones**: Siempre validar que el evento tiene los datos esperados antes de transformar
3. **Logging**: Incluir contexto (event_id, correlation_id, incident_id) en todos los logs
4. **Validación**: Las excepciones personalizadas se convierten automáticamente a respuestas HTTP apropiadas
