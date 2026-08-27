from src import create_app


def test_create_app_applies_test_configuration():
    """A test override must take precedence over environment settings."""
    app = create_app({"TESTING": True, "JWT_SECRET_KEY": "test-secret"})

    assert app.testing is True
    assert app.config["JWT_SECRET_KEY"] == "test-secret"


def test_create_app_uses_injected_event_producer():
    producer = object()

    app = create_app({"TESTING": True, "EVENT_PRODUCER": producer})

    assert app.extensions["event_producer"] is producer
