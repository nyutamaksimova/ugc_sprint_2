import pytest
from pydantic import ValidationError

from src.core.config import Settings


def test_settings_reads_explicit_values():
    settings = Settings(
        jwt_secret="secret-that-is-at-least-32-characters-long",
        jwt_algorithm="HS512",
        mongo_uri="mongodb://mongo:27017/?replicaSet=rs0",
        mongo_database="ugc_test",
    )

    assert settings.jwt_secret == "secret-that-is-at-least-32-characters-long"
    assert settings.mongo_database == "ugc_test"


def test_settings_requires_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError, match="Field required"):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret", ["change-me", "too-short"])
def test_settings_rejects_unsafe_jwt_secret(secret):
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(jwt_secret=secret)
