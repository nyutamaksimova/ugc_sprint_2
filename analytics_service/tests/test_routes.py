import jwt
import pytest

from src import create_app
from src.services.producer import KafkaUnavailableError


class ProducerStub:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[list[dict], str]] = []
        self.error = error

    def publish(self, events: list[dict], user_id: str) -> None:
        if self.error:
            raise self.error
        self.calls.append((events, user_id))


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "JWT_SECRET_KEY": "a" * 32})
    app.extensions["event_producer"] = ProducerStub()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    token = jwt.encode({"sub": "user-42"}, app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def event():
    return {
        "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "event_type": "click",
        "occurred_at": "2026-08-13T12:00:00Z",
        "session_id": "019ffafa-5fd5-7363-8154-84618a0104db",
        "payload": {"element": "movie_card"},
    }


def test_single_event_returns_202_and_publishes(client, app, auth_headers, event):
    response = client.post("/api/v1/events", headers=auth_headers, json=event)

    assert response.status_code == 202
    assert response.json == {"count": 1, "status": "accepted"}
    assert app.extensions["event_producer"].calls[0][1] == "user-42"


def test_invalid_batch_returns_indexes_and_does_not_publish(client, app, auth_headers):
    response = client.post("/api/v1/events/batch", headers=auth_headers, json=[{}, {}])

    assert response.status_code == 422
    assert [error["index"] for error in response.json["errors"]] == [0, 1]
    assert app.extensions["event_producer"].calls == []


def test_kafka_failure_returns_503(client, app, auth_headers, event):
    app.extensions["event_producer"] = ProducerStub(KafkaUnavailableError())

    response = client.post("/api/v1/events", headers=auth_headers, json=event)

    assert response.status_code == 503
    assert response.json["code"] == "kafka_unavailable"
