"""
Utilidades compartidas: validaciones, manejo de errores, etc.
"""

from typing import Optional, List
from schemas import ErrorResponseSchema, ErrorDetailSchema
from constants import VALID_STATUSES, VALID_SEVERITIES


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    
    def __init__(self, message: str, details: Optional[List[dict]] = None):
        self.message = message
        self.details = details or []
        super().__init__(self.message)
    
    def to_response(self) -> ErrorResponseSchema:
        """Convierte el error a una respuesta estructurada."""
        error_details = [
            ErrorDetailSchema(field=d.get('field', ''), message=d.get('message', ''))
            for d in self.details
        ]
        return ErrorResponseSchema(message=self.message, details=error_details or None)


def validate_status(status: str) -> tuple[bool, Optional[str]]:
    """
    Valida que el estado sea válido.
    
    Args:
        status: Estado a validar
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if status not in VALID_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
    return True, None


def validate_severity(severity: str) -> tuple[bool, Optional[str]]:
    """
    Valida que la severidad sea válida.
    
    Args:
        severity: Severidad a validar
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if severity not in VALID_SEVERITIES:
        return False, f"Invalid severity. Must be one of: {', '.join(VALID_SEVERITIES)}"
    return True, None


def validate_create_incident_request(
    title: str,
    description: str,
    severity: str
) -> tuple[bool, Optional[ValidationError]]:
    """
    Valida una solicitud de creación de incidente.
    
    Args:
        title: Título del incidente
        description: Descripción del incidente
        severity: Severidad del incidente
    
    Returns:
        Tupla (es_válido, error_object_o_None)
    """
    details = []
    
    if not title or not title.strip():
        details.append({'field': 'title', 'message': 'Title is required and cannot be empty'})
    
    if not description or not description.strip():
        details.append({'field': 'description', 'message': 'Description is required and cannot be empty'})
    
    is_valid_severity, error_msg = validate_severity(severity)
    if not is_valid_severity:
        details.append({'field': 'severity', 'message': error_msg})
    
    if details:
        return False, ValidationError("Validation error", details)
    
    return True, None


def validate_status_change(new_status: str) -> tuple[bool, Optional[ValidationError]]:
    """
    Valida un cambio de estado.
    
    Args:
        new_status: Nuevo estado
    
    Returns:
        Tupla (es_válido, error_object_o_None)
    """
    is_valid, error_msg = validate_status(new_status)
    
    if not is_valid:
        error = ValidationError("Validation error", [{'field': 'status', 'message': error_msg}])
        return False, error
    
    return True, None


def validate_severity_change(new_severity: str) -> tuple[bool, Optional[ValidationError]]:
    """
    Valida un cambio de severidad.
    
    Args:
        new_severity: Nueva severidad
    
    Returns:
        Tupla (es_válido, error_object_o_None)
    """
    is_valid, error_msg = validate_severity(new_severity)
    
    if not is_valid:
        error = ValidationError("Validation error", [{'field': 'severity', 'message': error_msg}])
        return False, error
    
    return True, None
