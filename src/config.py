import os
import logging

from pydantic import Field, AnyHttpUrl, PostgresDsn, AnyUrl
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_LOG_FILE = "downloaded_files.txt"


class Settings(BaseSettings):
    # DATABASE_URL: PostgresDsn TODO: проверить возможность замены 5-ти полей на одно.
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

    infura_url: AnyHttpUrl = Field(..., description="Infura URL for Ethereum API")
    infura_url_ws: AnyUrl = Field(..., description="Infura URL for WebSocket API")
    infura_key: str = Field(..., description="Infura project key")
    cache_expiry: int = Field(default=60, description="Cache expiry time in seconds")


settings = Settings()


def get_db_url():
    return (f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
