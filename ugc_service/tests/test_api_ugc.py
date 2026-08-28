from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from src.api.v1.ratings import user_id
from src.api.v1.ugc import service
from src.main import create_app


@asynccontextmanager
async def empty_lifespan(_: FastAPI):
    yield


class FakeUgcService:
    def __init__(self):
        self.bookmarks = []

    async def put_bookmark(self, user_id, film_id):
        self.bookmarks.append((str(user_id), str(film_id)))

    async def delete_bookmark(self, user_id, film_id):
        return False

    async def bookmarks(self, user_id, limit, cursor):
        return {"items": [], "next_cursor": None}

    async def create_review(self, user_id, film_id, text, author_score):
        return {"id": "review", "text": text, "author_score": author_score}

    async def list_reviews(self, film_id, sort, limit, cursor):
        return {"items": [], "next_cursor": None}

    async def vote(self, user_id, review_id, value):
        return {"id": str(review_id), "vote_score": value}


def test_ugc_crud_routes_use_overridden_dependencies():
    fake = FakeUgcService()
    app = create_app(lifespan_context=empty_lifespan)
    app.dependency_overrides[user_id] = uuid4
    app.dependency_overrides[service] = lambda: fake
    film_id = uuid4()

    with TestClient(app) as client:
        assert client.put(f"/api/v1/users/me/bookmarks/{film_id}").status_code == 204
        review = client.post(f"/api/v1/films/{film_id}/reviews", json={"text": "Good"})
        vote = client.put(f"/api/v1/reviews/{uuid4()}/votes/me", json={"value": 1})

    assert fake.bookmarks
    assert review.status_code == 201
    assert vote.status_code == 200


def test_mongo_error_returns_service_unavailable():
    app = create_app(lifespan_context=empty_lifespan)
    app.dependency_overrides[user_id] = uuid4

    class BrokenService(FakeUgcService):
        async def put_bookmark(self, user_id, film_id):
            raise PyMongoError("database unavailable")

    app.dependency_overrides[service] = BrokenService

    with TestClient(app) as client:
        response = client.put(f"/api/v1/users/me/bookmarks/{uuid4()}")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
