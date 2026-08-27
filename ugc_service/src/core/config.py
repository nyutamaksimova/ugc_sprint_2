from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    mongo_uri: str = "mongodb://localhost:27017/?directConnection=true"
    mongo_database: str = "ugc"
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
