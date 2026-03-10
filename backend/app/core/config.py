"""Настройки приложения из переменных окружения."""

from urllib.parse import urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/library"
    database_host: str | None = None  # переопределение хоста БД (напр. 127.0.0.1 для --network host)
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 дней
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def effective_database_url(self) -> str:
        """URL БД с учётом DATABASE_HOST (для миграций с --network host)."""
        if not self.database_host:
            return self.database_url
        parsed = urlparse(self.database_url)
        netloc = parsed.netloc
        if "@" in netloc:
            userinfo, hostport = netloc.rsplit("@", 1)
            port_part = f":{hostport.rsplit(':', 1)[1]}" if ":" in hostport else ""
            new_netloc = f"{userinfo}@{self.database_host}{port_part}"
        else:
            port_part = f":{netloc.rsplit(':', 1)[1]}" if ":" in netloc else ""
            new_netloc = f"{self.database_host}{port_part}"
        return urlunparse(parsed._replace(netloc=new_netloc))

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
