from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://shibofinance:shibofinance@db:5432/shibofinance"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False


settings = Settings()
