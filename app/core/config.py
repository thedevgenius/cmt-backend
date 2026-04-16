from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "App"
    DEBUG: bool = False

    DATABASE_URL: str

    GOOGLE_MAPS_API_KEY: str
    MSG_WIDGET_ID: str
    MSG_AUTH_KEY: str

    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()