from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    firebase_credentials_path: str = "./serviceAccountKey.json"
    firebase_project_id:       str = ""
    firebase_database_url:     str = ""
    app_env:                   str = "development"
    frontend_origin:           str = "http://localhost:3000"
    match_limit:               int = 20

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
