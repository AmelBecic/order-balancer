# backend/app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List # <-- Import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", env_file_encoding='utf-8')

    # Application settings
    API_V1_STR: str
    SECRET_KEY: str

    # Database settings
    MONGODB_URL: str
    DATABASE_NAME: str

    # RabbitMQ settings
    RABBITMQ_URL: str
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] # <-- Add this line

settings = Settings()