from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/farmai?charset=utf8mb4"
    TRACKING_DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/farmai_tracking?charset=utf8mb4"
    
    # Server
    # Bind only to localhost for local-only access
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"


settings = Settings()
