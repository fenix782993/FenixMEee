from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Fenix Messenger"
    database_url: str = "sqlite:///./fenix.db"
    jwt_secret: str = "CHANGE_THIS_IN_PRODUCTION_USE_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 30
    upload_dir: str = "./uploads"
    cors_origins: str = "*"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
