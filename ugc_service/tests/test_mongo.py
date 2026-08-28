import asyncio

from src.db.mongo import ensure_indexes


class FakeCollection:
    def __init__(self):
        self.calls = []

    async def create_index(self, keys, **kwargs):
        self.calls.append((keys, kwargs))


class FakeDatabase:
    def __init__(self):
        for name in ("ratings", "rating_summaries", "bookmarks", "reviews", "review_votes"):
            setattr(self, name, FakeCollection())


def test_ensure_indexes_creates_unique_rating_relation():
    database = FakeDatabase()

    asyncio.run(ensure_indexes(database))

    assert (
        [("user_id", 1), ("film_id", 1)],
        {"unique": True, "name": "rating_user_film"},
    ) in database.ratings.calls


def test_ensure_indexes_creates_review_author_score_index():
    database = FakeDatabase()

    asyncio.run(ensure_indexes(database))

    assert (
        [("film_id", 1), ("author_score", -1), ("_id", 1)],
        {"name": "reviews_film_author_score"},
    ) in database.reviews.calls
