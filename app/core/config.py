from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://motorq:motorq@localhost:5432/motorq"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://motorq:motorq@localhost:5672/"

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()