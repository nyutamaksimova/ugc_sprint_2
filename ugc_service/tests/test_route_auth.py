from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import create_app


@asynccontextmanager
async def empty_lifespan(_: FastAPI):
    yield


@pytest.mark.parametrize(
    "path",
    [
        f"/api/v1/films/{uuid4()}/ratings/summary",
        f"/api/v1/films/{uuid4()}/reviews",
    ],
)
def test_read_ugc_routes_require_bearer_token(path: str):
    with TestClient(create_app(lifespan_context=empty_lifespan)) as client:
        response = client.get(path)

    assert response.status_code == 403
