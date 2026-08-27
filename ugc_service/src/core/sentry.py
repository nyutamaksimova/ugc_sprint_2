import sentry_sdk


def init_sentry(*, dsn: str, environment: str) -> None:
    if dsn:
        sentry_sdk.init(dsn=dsn, environment=environment, traces_sample_rate=0.1)
