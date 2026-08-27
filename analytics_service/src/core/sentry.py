import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def init_sentry(*, dsn: str, environment: str) -> None:
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )
