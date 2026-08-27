from unittest.mock import patch

from src.core.sentry import init_sentry


def test_sentry_is_not_initialized_without_dsn():
    with patch("src.core.sentry.sentry_sdk.init") as init:
        init_sentry(dsn="", environment="development")

    init.assert_not_called()
