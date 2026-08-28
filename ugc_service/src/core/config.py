from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    mongo_uri: str = "mongodb://localhost:27017/?directConnection=true"
    mongo_database: str = "ugc"
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if value == "change-me" or len(value) < 32:
            raise ValueError(
                "JWT_SECRET must not be 'change-me' and must be at least 32 characters long"
            )
        return value


settings = Settings()  # type: ignore[call-arg]  # JWT_SECRET is read from the environment.
