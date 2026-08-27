import jwt
from flask import Flask

from src.core.auth import require_user


def make_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        JWT_SECRET_KEY="test-secret-key-with-at-least-32-bytes",
        JWT_ALGORITHM="HS256",
    )

    @app.get("/private")
    @require_user
    def private(user_id: str):
        return {"user_id": user_id}

    return app


def test_valid_bearer_token_injects_subject():
    token = jwt.encode(
        {"sub": "user-42"},
        "test-secret-key-with-at-least-32-bytes",
        algorithm="HS256",
    )

    response = make_app().test_client().get(
        "/private", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json == {"user_id": "user-42"}


def test_missing_bearer_token_returns_401():
    response = make_app().test_client().get("/private")

    assert response.status_code == 401
    assert response.json == {
        "code": "unauthorized",
        "message": "Valid bearer token is required",
    }


def test_invalid_bearer_token_returns_401():
    response = make_app().test_client().get(
        "/private", headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert response.status_code == 401
