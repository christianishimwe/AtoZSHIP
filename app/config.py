from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
    env_file=".env",
    env_ignore_empty=True,
    extra="ignore",
)


class DatabaseSettings(BaseSettings):
    POSTGRES_URL: str
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    model_config = _base_config


class RedisSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int

    model_config = _base_config

    def REDIS_URL(self, db: int) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{str(db)}"


class AppSettings(BaseSettings):
    APP_BASE_URL: str = "http://localhost:8000"

    model_config = _base_config


class NotificationSettings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    VALIDATE_CERTS: bool = True
    model_config = _base_config


database_settings = DatabaseSettings()
redis_settings = RedisSettings()
notification_settings = NotificationSettings()
app_settings = AppSettings()
