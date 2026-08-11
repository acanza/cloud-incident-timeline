"""
Configuración de la aplicación desde variables de entorno.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # AWS
    aws_region: str = os.getenv('AWS_REGION', 'eu-west-3')
    incidents_table_name: str = os.getenv('INCIDENTS_TABLE_NAME', 'cloud-incident-timeline-dev-incidents')
    event_bus_name: str = os.getenv('EVENT_BUS_NAME', 'cloud-incident-timeline-dev-event-bus')
    
    # Service
    service_name: str = os.getenv('SERVICE_NAME', 'incident-service')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Server
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8001))
    
    class Config:
        env_file = '.env'
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
