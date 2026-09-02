# Timeline Service - Phase 4: Event Processing & SQS Consumer

## Descripción General

La Fase 4 implementa el consumer de SQS que poll la cola de timeline, recibe eventos y los procesa de forma asincrónica.

## Arquitectura

```
SQS Queue (cloud-incident-timeline-dev-timeline-queue)
    ↓
SQSConsumer.start()
    ├─ Long polling (WaitTimeSeconds=20)
    ├─ Receive batch (MaxMessages=10)
    │
    └─ Para cada mensaje:
        ├─ MessageHandler.process_message()
        │   ├─ Parse JSON body
        │   ├─ TimelineService.process_event()
        │   ├─ En caso de éxito: delete_message()
        │   └─ En caso de error: leave in queue (retry)
        │
        └─ Repetir polling
```

## Componentes

### 1. **MessageHandler** (`src/services/message_handler.py`)

Maneja el procesamiento de mensajes individuales de SQS.

**Responsabilidades:**
- Parsear cuerpo del mensaje SQS (JSON)
- Delegación a TimelineService
- Manejo de errores
- Eliminación de mensajes exitosos
- Logging estructurado

#### Métodos Principales

```python
handler = MessageHandler()

# Procesar un mensaje de SQS
success = handler.process_message(message)
# → True si se procesó y eliminó
# → False si debe reintentarse
```

#### Flujo de Procesamiento de un Mensaje

```
1. Extraer message_id y receipt_handle
2. Parsear body como JSON (event)
3. Validar estructura de mensaje
4. Delegación a TimelineService.process_event()
   ├─ Si retorna TimelineEntry → delete_message()
   ├─ Si retorna None (duplicado) → delete_message() (idempotente)
   └─ Si lanza excepción → No eliminar (retry)
5. Log del resultado
```

**Manejo de Errores:**

| Error | Acción | Razón |
|-------|--------|-------|
| JSON inválido | Eliminar | No se puede procesar, no retry |
| Estructura inválida | Eliminar | Malformed, no va a cambiar |
| ValidationError | No eliminar | Cliente puede corregir |
| EventProcessingError | No eliminar | Error temporal, retry podría funcionar |
| Duplicado | Eliminar | Ya procesado, idempotente |

**Logging:**

```json
{
  "level": "INFO",
  "message": "Event processed successfully, creating timeline entry",
  "message_id": "msg-123",
  "incident_id": "inc-001",
  "event_id": "evt-001"
}
```

### 2. **SQSConsumer** (`src/services/sqs_consumer.py`)

Consumer loop que poll SQS continuamente y procesa eventos.

**Responsabilidades:**
- Polling continuo de SQS (long polling)
- Recibir batches de mensajes
- Procesar cada mensaje
- Manejo de señales (Ctrl+C, SIGTERM)
- Shutdown graceful
- Estadísticas de ejecución

#### Métodos Principales

```python
consumer = SQSConsumer()

# Iniciar el consumer (bloquea indefinidamente)
consumer.start()
# Escucha Ctrl+C o SIGTERM para shutdown

# Obtener estadísticas
stats = consumer.get_stats()
# → {"processed": 42, "failed": 2, "running": True}
```

#### Configuración de Long Polling

```python
# De constants.py:
SQS_MAX_MESSAGES = 10        # Recibir máximo 10 mensajes por poll
SQS_WAIT_TIME = 20           # Esperar 20 segundos si cola vacía
```

**Beneficios de Long Polling:**
- ✅ Reduce API calls (vs short polling)
- ✅ Reduce latencia (vs polling frecuente)
- ✅ Ahorra costos de AWS
- ✅ Consume menos CPU

#### Flujo de Ejecución

```
1. Inicializar SQSConsumer
2. Registrar signal handlers (SIGINT, SIGTERM)
3. Entrar en polling loop:
   
   while running:
       messages = receive_messages(QueueUrl, MaxMessages=10, WaitTime=20)
       
       for message in messages:
           if not running: break
           process_single_message(message)
               ↓ delega a MessageHandler

4. Esperar Ctrl+C o SIGTERM
5. Shutdown graceful:
   - Set running = False
   - Wait 1 segundo para completar ops
   - Log estadísticas finales
   - Exit
```

#### Manejo de Señales

```python
# Ctrl+C (SIGINT) o SIGTERM
Signal received → running = False → Exit loop → Shutdown
```

El consumer respeta señales del sistema operativo:
```bash
# Graceful shutdown
kill -TERM <pid>

# Inmediato en terminal
Ctrl+C
```

#### Estadísticas

El consumer mantiene contadores:
```python
consumer.processed_count  # Mensajes procesados exitosamente
consumer.failed_count     # Mensajes con error (no eliminados)
consumer.running          # Estado actual
```

## Conformidad con Especificaciones

✅ **Event Consumer Behavior** (Sec. 8)
- Consume eventos del SQS queue dedicado
- Procesa tipos de eventos requeridos
- Transforma a timeline entries

✅ **Idempotency** (Sec. 9)
- No crea duplicados
- SQS retries manejados gracefully
- source_event_id usado para deduplicación

✅ **Error Handling** (Sec. 10)
- Logging estructurado
- Errores de procesamiento → No eliminar (retry)
- Errores de formato → Eliminar (don't retry)

## Flujo Ejemplo End-to-End

### Escenario 1: Evento válido, procesamiento exitoso

```
SQS Message Body:
{
  "event_type": "IncidentCreated",
  "event_id": "evt-001",
  "data": {"incident_id": "inc-001", "severity": "HIGH"}
}

↓ MessageHandler.process_message()
  ↓ TimelineService.process_event()
    ↓ Crea TimelineEntry
    ↓ Persiste en DynamoDB
  ↓ Retorna TimelineEntry
↓ handler.delete_message(receipt_handle)

Resultado: ✅ Mensaje eliminado, Timeline entry creada
Logs: "Event processed successfully"
```

### Escenario 2: Duplicado (SQS retry)

```
SQS Message Body (mismo que antes):
{
  "event_type": "IncidentCreated",
  "event_id": "evt-001",
  "data": {"incident_id": "inc-001"}
}

↓ MessageHandler.process_message()
  ↓ TimelineService.process_event()
    ↓ Verifica: entry_exists_by_source_event("inc-001", "evt-001")
    ↓ Retorna: True (ya existe)
    ↓ Retorna: None (indicando duplicado)
  ↓ Retorna None
↓ handler.delete_message(receipt_handle)

Resultado: ✅ Mensaje eliminado (no duplicado creado)
Logs: "Event was duplicate, skipped"
```

### Escenario 3: Error de procesamiento

```
SQS Message Body:
{
  "event_type": "IncidentStatusChanged",
  "event_id": "evt-002",
  "data": {"incident_id": "inc-001", ...}
}

↓ MessageHandler.process_message()
  ↓ TimelineService.process_event()
    ↓ TimelineRepository.create_entry() → DynamoDB Error
    ↓ Lanza: DynamoDBError
  ↓ Catch exception
↓ Retorna: False (no eliminar)

Resultado: ❌ Mensaje NO eliminado
Logs: "Service error processing message"
→ SQS reintentar según redrive policy (después de visibility timeout)
```

### Escenario 4: JSON inválido

```
SQS Message Body:
{
  "invalid": "json"  // Falta event_type, etc.
}

↓ MessageHandler.process_message()
  ↓ Valida estructura
  ↓ Falta campo requerido
  ↓ Lanza: ValidationError
  ↓ Catch exception
↓ handler.delete_message(receipt_handle)

Resultado: ✅ Mensaje eliminado
Logs: "Invalid event structure"
→ No retry (malformado no va a cambiar)
```

## Configuración de DLQ (Dead Letter Queue)

Según especificaciones, SQS tiene DLQ asociada:
```
cloud-incident-timeline-dev-timeline-dlq
```

**Redrive Policy:**
- Máximo intentos: 3 (típico)
- Visibility timeout: 5 minutos
- Después de 3 fallos → Mensaje a DLQ

**Recomendación:**
- Monitorear DLQ regularmente
- Alertas si mensajes llegan a DLQ
- Investigar causa de fallos
- Manual replay desde DLQ después de fix

## Logging Estructurado

Todos los logs incluyen contexto relevante:

```json
{
  "timestamp": "2026-07-30T08:00:00Z",
  "level": "INFO",
  "logger": "timeline_service.services.sqs_consumer",
  "message": "Received 5 messages from queue",
  "queue": "cloud-incident-timeline-dev-timeline-queue",
  "count": 5
}
```

## Monitoreo en Producción

**Métricas clave:**
```
consumer.processed_count  → Eventos procesados
consumer.failed_count     → Eventos fallidos (reintentos en progreso)
Messages in queue         → Backlog (CloudWatch)
Messages in DLQ           → Indica problemas
Visibility timeout        → Tiempo para procesar mensaje
```

**Alertas recomendadas:**
- DLQ tiene mensajes
- Processed count estancado
- Failed count creciendo
- Consumer no responde a signals

## Próximas Fases

- **Fase 5**: HTTP API (endpoints GET/POST)
- **Fase 6**: Dockerization (multi-process: FastAPI + Consumer)
- **Fase 7**: Documentation & README

## Notas de Implementación

1. **Graceful Shutdown**: El consumer respeta SIGTERM/SIGINT
2. **Idempotencia**: Duplicados se eliminan, no se retienen
3. **Errores Temporales**: No se eliminan, SQS reintenta automáticamente
4. **Errores Permanentes**: Se eliminan (malformed) para no bloquear cola
5. **Logging**: Context incluye message_id, event_id, incident_id para tracing
6. **Performance**: Long polling reduce costos y latencia
7. **Backpressure**: Si procesamiento lento, mensajes se acumulan en SQS (queue scales automatically)
