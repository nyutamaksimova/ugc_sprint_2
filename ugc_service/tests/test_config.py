from src.core.config import Settings


def test_settings_reads_explicit_values():
    settings = Settings(
        jwt_secret="secret",
        jwt_algorithm="HS512",
        mongo_uri="mongodb://mongo:27017/?replicaSet=rs0",
        mongo_database="ugc_test",
    )

    assert settings.jwt_secret == "secret"
    assert settings.mongo_database == "ugc_test"
