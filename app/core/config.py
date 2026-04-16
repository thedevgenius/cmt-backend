from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "App"
    DEBUG: bool = False

    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()