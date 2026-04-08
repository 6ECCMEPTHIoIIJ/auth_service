from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from time_units import DAY, MIN


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(description="URL базы данных; env: DATABASE_URL")
    redis_url: str = Field(description="URL Redis; env: REDIS_URL")

    jwt_secret: str = Field(
        min_length=16, description="Секрет подписи JWT; env: JWT_SECRET"
    )
    jwt_algorithm: str = Field(
        default="HS256", description="Алгоритм подписи JWT; env: JWT_ALGORITHM"
    )
    access_token_ttl_seconds: int = Field(
        default=int(15 * MIN.secs),
        description="Время жизни access токена в секундах; env: ACCESS_TOKEN_TTL_SECONDS",
    )
    refresh_token_ttl_seconds: int = Field(
        default=int(7 * DAY.secs),
        description="Время жизни refresh токена в секундах; env: REFRESH_TOKEN_TTL_SECONDS",
    )

    internal_api_key: str = Field(
        min_length=8, description="Ключ internal API; env: INTERNAL_API_KEY"
    )

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    csrf_cookie_name: str = "csrf_token"


settings = Settings()
