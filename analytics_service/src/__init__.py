from flask import Flask

from src.core.config import Settings
from src.core.sentry import init_sentry


def create_app(test_config: dict | None = None) -> Flask:
    settings = Settings.from_env()
    init_sentry(dsn=settings.sentry_dsn, environment=settings.sentry_environment)
    app = Flask(__name__)
    app.config.from_mapping(
        JWT_SECRET_KEY=settings.jwt_secret_key,
        JWT_ALGORITHM=settings.jwt_algorithm,
        KAFKA_BOOTSTRAP_SERVERS=settings.kafka_bootstrap_servers,
        MAX_CONTENT_LENGTH=settings.max_content_length,
    )
    if test_config:
        app.config.update(test_config)
    from src.services.producer import build_event_producer
    from src.api.routes import bp, register_error_handlers

    app.extensions["event_producer"] = app.config.get("EVENT_PRODUCER") or build_event_producer(
        app.config["KAFKA_BOOTSTRAP_SERVERS"]
    )
    app.register_blueprint(bp)
    register_error_handlers(app)
    return app
