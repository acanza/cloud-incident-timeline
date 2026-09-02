# Timeline Service - Phase 3: DynamoDB Access Layer

## Descripción General

La Fase 3 implementa la capa de persistencia y lógica de negocio. Se encarga de todas las interacciones con DynamoDB y la orquestación del procesamiento de eventos.

## Arquitectura

```
Event (from SQS)
    ↓
TimelineService.process_event()
    ├─ Validación de estructura
    ├─ Verificación de tipo consumible
    ├─ Parsing a modelo tipado
    ├─ Verificación de idempotencia
    ├─ Transformación a mensaje legible
    ├─ Validación de entrada
    └─ Persistencia via TimelineRepository
        └─ DynamoDB put_item
```

## Componentes

### 1. **TimelineRepository** (`src/services/timeline_repository.py`)

Capa de acceso directo a DynamoDB. Responsabilidades:

#### Métodos Principales

```python
repository = TimelineRepository()

# Crear entrada de timeline
repository.create_entry(timeline_entry: TimelineEntry) -> bool

# Obtener todas las entradas de un incidente
entries = repository.get_entries_by_incident(incident_id: str) -> List[TimelineEntry]

# Verificar si una entrada ya existe (idempotencia)
exists = repository.entry_exists_by_source_event(
    incident_id: str, 
    source_event_id: str
) -> bool

# Contar entradas para un incidente
count = repository.get_entry_count_by_incident(incident_id: str) -> int
```

**Operaciones DynamoDB:**

| Operación | Método | DynamoDB Op | Notas |
|-----------|--------|-------------|-------|
| Crear | `create_entry()` | `put_item` | Inserta nueva entrada de timeline |
| Leer | `get_entries_by_incident()` | `query` | Usa PK + SK para obtener en orden cronológico |
| Verificar | `entry_exists_by_source_event()` | `query` + filter | Idempotencia: evita duplicados |
| Contar | `get_entry_count_by_incident()` | `query` (COUNT) | Para métricas/debugging |

**Estructura de Items en DynamoDB:**

```
PK (Partition Key):  incident_id
SK (Sort Key):       created_at#timeline_entry_id

Atributos:
  - incident_id (string)
  - created_at (string, ISO format)
  - timeline_entry_id (string, UUID)
  - message (string, hasta 1000 chars)
  - event_type (string, tipo de evento)
  - source_event_id (string, para idempotencia)

Índices:
  - GSI1PK: source_event_id (opcional, para búsquedas por evento)
```

**Manejo de Errores:**

Todas las excepciones de DynamoDB se capturan y se convierten a `DynamoDBError` con contexto:

```python
try:
    repository.create_entry(entry)
except DynamoDBError as e:
    # Error info: message, error_code, details (resource name)
    logger.error(f"DynamoDB error: {e.message}")
```

### 2. **TimelineService** (`src/services/timeline_service.py`)

Servicio de lógica de negocio que orquesta la validación, transformación y persistencia.

#### Flujo de Procesamiento de Eventos

```python
service = TimelineService()

# Procesar evento de SQS
timeline_entry = service.process_event(raw_event)
# Retorna: TimelineEntry | None (si duplicado) | Excepción si error
```

**Pasos del proceso:**

1. **Validación de Estructura**
   - Verificar presencia de campos requeridos (version, event_id, event_type, etc.)
   - Validar version = "1.0"

2. **Verificación de Tipo Consumible**
   - Solo procesa: IncidentCreated, IncidentStatusChanged, IncidentSeverityChanged, IncidentResolved
   - Ignora otros eventos

3. **Parsing a Modelo Tipado**
   - Convierte raw_event a evento específico (IncidentCreatedEvent, etc.)
   - Validación automática de Pydantic

4. **Extracción de Datos**
   - Obtiene incident_id de event.data
   - Obtiene source_event_id de event.event_id

5. **Verificación de Idempotencia**
   - Consulta si ya existe entrada con este source_event_id
   - Si existe: retorna None (no es error, es normal en SQS con reintentos)
   - Si no existe: continúa

6. **Transformación a Mensaje**
   - Usa EventTransformer para convertir evento a mensaje legible
   - Ejemplo: "Incident created with HIGH severity and OPEN status."

7. **Creación de Entrada**
   - Construye TimelineEntry con:
     - incident_id: desde event.data
     - timeline_entry_id: generado (UUID)
     - created_at: timestamp actual en UTC
     - message: transformado en paso 6
     - event_type: tipo del evento
     - source_event_id: para idempotencia futura

8. **Validación**
   - Valida que la entrada cumple esquema requerido

9. **Persistencia**
   - Llama a repository.create_entry()
   - Retorna TimelineEntry creada

**Ejemplo de Uso:**

```python
raw_event = {
    "version": "1.0",
    "event_id": "evt-001",
    "event_type": "IncidentCreated",
    "source": "incident-service",
    "occurred_at": "2026-07-30T08:00:00Z",
    "correlation_id": "corr-001",
    "actor": {"user_id": "user-001"},
    "data": {
        "incident_id": "inc-001",
        "title": "API latency",
        "severity": "HIGH",
        "status": "OPEN"
    }
}

service = TimelineService()
entry = service.process_event(raw_event)

if entry:
    print(f"Created timeline entry: {entry.timeline_entry_id}")
    # Output: "Incident created with HIGH severity and OPEN status."
else:
    print("Event was duplicate, skipped")
```

#### Métodos Principales

```python
# Procesar evento de SQS
entry = service.process_event(raw_event: dict) -> Optional[TimelineEntry]

# Obtener timeline de un incidente
entries = service.get_timeline(incident_id: str) -> List[TimelineEntry]

# Crear entrada manual desde comentario de usuario
entry = service.create_comment_entry(
    incident_id: str,
    comment: str,
    user_id: Optional[str] = None
) -> TimelineEntry
```

**Manejo de Excepciones:**

```python
try:
    entry = service.process_event(raw_event)
except ValidationError:
    # Estructura de evento inválida → HTTP 400
    pass
except EventProcessingError:
    # Error inesperado en procesamiento → HTTP 500
    pass
except IdempotencyError:
    # Violación de idempotencia con conflicto → HTTP 409
    pass
```

## Conformidad con Especificaciones

✅ **Data Models** (Sec. 6)
- Timeline table con estructura correcta
- Campos recomendados presentes

✅ **Event Consumer Behavior** (Sec. 8)
- Procesa los 4 eventos requeridos
- Transforma a mensajes legibles
- Manejo correcto de datos de evento

✅ **Idempotency** (Sec. 9)
- Verifica source_event_id antes de crear
- No crea duplicados
- Retorna None para duplicados (no es error)

✅ **Error Handling** (Sec. 10)
- Excepciones personalizadas
- Logging estructurado
- Manejo robusto de fallos de DynamoDB

## Logging

Todas las operaciones registran contexto:

```json
{
  "timestamp": "2026-07-30T08:00:00Z",
  "level": "INFO",
  "message": "Timeline entry created successfully",
  "incident_id": "inc-001",
  "timeline_entry_id": "tl-abc123",
  "source_event_id": "evt-001",
  "correlation_id": "corr-001"
}
```

## Próximas Fases

- **Fase 4**: Procesador de eventos (consumo de SQS)
- **Fase 5**: Consumer SQS (polling loop)
- **Fase 6**: API HTTP (GET /health, GET /incidents/{id}/timeline, POST /incidents/{id}/timeline/comments)

## Notas Importantes

1. **Idempotencia**: Las duplicatas se ignoran silenciosamente (retorna None), no es error
2. **Ordering**: Results de query siempre están en orden cronológico (SK = created_at#id)
3. **Performance**: Query por incident_id es O(log n), scan es O(n) - siempre usar query
4. **Transactional**: Cada entrada es independiente, no hay transacciones multi-item
5. **Retention**: No hay limpieza automática, las entradas son inmutables una vez creadas
