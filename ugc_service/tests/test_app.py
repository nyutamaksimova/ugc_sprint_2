from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import create_app


@asynccontextmanager
async def empty_lifespan(_: FastAPI):
    yield


def test_health_endpoint_returns_ok():
    with TestClient(create_app(lifespan_context=empty_lifespan)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
