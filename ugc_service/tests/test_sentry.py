from unittest.mock import patch

from src.core.sentry import init_sentry


def test_sentry_is_not_initialized_without_dsn():
    with patch("src.core.sentry.sentry_sdk.init") as init:
        init_sentry(dsn="", environment="development")

    init.assert_not_called()


def test_sentry_uses_dsn_and_environment():
    with patch("src.core.sentry.sentry_sdk.init") as init:
        init_sentry(dsn="https://key@example.invalid/1", environment="development")

    init.assert_called_once_with(
        dsn="https://key@example.invalid/1", environment="development", traces_sample_rate=0.1
    )
