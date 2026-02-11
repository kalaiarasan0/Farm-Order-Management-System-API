import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ASYNC_DATABASE_URL: str = os.getenv("ASYNC_DATABASE_URL")
    USER_DATABASE_URL: str = os.getenv("USER_DATABASE_URL")
    ASYNC_USER_DATABASE_URL: str = os.getenv("ASYNC_USER_DATABASE_URL")

    FERNET_KEY: str = os.getenv("FERNET_KEY")

    # Server
    # Bind only to localhost for local-only access
    HOST: str = os.getenv("HOST")
    PORT: int = int(os.getenv("PORT"))

    class Config:
        env_file = ".env"


settings = Settings()
