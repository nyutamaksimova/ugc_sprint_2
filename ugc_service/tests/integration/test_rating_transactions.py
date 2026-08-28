import asyncio
import os
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.db.mongo import ensure_indexes
from src.services.ratings import RatingService
from src.services.ugc import UgcService

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    pytest.skip("MONGO_URI is required for MongoDB integration tests", allow_module_level=True)


async def _actual_summary(database, film_id):
    cursor = database.ratings.aggregate(
        [
            {"$match": {"film_id": str(film_id)}},
            {
                "$group": {
                    "_id": None,
                    "score_count": {"$sum": 1},
                    "score_sum": {"$sum": "$score"},
                    "likes_count": {"$sum": {"$cond": [{"$eq": ["$score", 10]}, 1, 0]}},
                    "dislikes_count": {"$sum": {"$cond": [{"$eq": ["$score", 0]}, 1, 0]}},
                }
            },
        ]
    )
    rows = await cursor.to_list(length=1)
    return (
        rows[0]
        if rows
        else {
            "score_count": 0,
            "score_sum": 0,
            "likes_count": 0,
            "dislikes_count": 0,
        }
    )


async def _run_with_database(scenario):
    client = AsyncIOMotorClient(MONGO_URI)
    database = client[f"ugc_rating_transactions_{uuid4().hex}"]
    try:
        await ensure_indexes(database)
        await scenario(database, client)
    finally:
        await client.drop_database(database.name)
        client.close()


@pytest.mark.integration
def test_concurrent_put_keeps_summary_in_sync():
    async def scenario(database, client):
        service = RatingService(database, client)
        user_id = uuid4()
        film_id = uuid4()

        await asyncio.gather(*(service.put(user_id, film_id, score) for score in (0, 10) * 10))

        expected = await _actual_summary(database, film_id)
        actual = await database.rating_summaries.find_one({"film_id": str(film_id)})
        assert actual is not None
        for field in ("score_count", "score_sum", "likes_count", "dislikes_count"):
            assert actual[field] == expected[field]

    asyncio.run(_run_with_database(scenario))


@pytest.mark.integration
def test_concurrent_delete_keeps_summary_in_sync():
    async def scenario(database, client):
        service = RatingService(database, client)
        user_id = uuid4()
        film_id = uuid4()
        await service.put(user_id, film_id, 10)

        await asyncio.gather(*(service.delete(user_id, film_id) for _ in range(10)))

        expected = await _actual_summary(database, film_id)
        actual = await database.rating_summaries.find_one({"film_id": str(film_id)})
        assert actual is not None
        for field in ("score_count", "score_sum", "likes_count", "dislikes_count"):
            assert actual[field] == expected[field]

    asyncio.run(_run_with_database(scenario))


@pytest.mark.integration
def test_vote_for_missing_review_does_not_leave_orphan_vote():
    async def scenario(database, client):
        service = UgcService(database, client)
        review_id = uuid4()

        assert await service.vote(uuid4(), review_id, 1) is None
        assert await database.review_votes.count_documents({"review_id": str(review_id)}) == 0

    asyncio.run(_run_with_database(scenario))


@pytest.mark.integration
def test_concurrent_votes_and_deletes_keep_vote_score_in_sync():
    async def scenario(database, client):
        ratings = UgcService(database, client)
        review_id = uuid4()
        await database.reviews.insert_one({"_id": str(review_id), "vote_score": 0})
        users = [uuid4() for _ in range(20)]
        values = (1, -1) * 10

        await asyncio.gather(
            *(ratings.vote(user_id, review_id, value) for user_id, value in zip(users, values))
        )

        review = await database.reviews.find_one({"_id": str(review_id)})
        assert review["vote_score"] == sum(values)
        assert await database.review_votes.count_documents({"review_id": str(review_id)}) == 20

        await asyncio.gather(*(ratings.delete_vote(user_id, review_id) for user_id in users))

        review = await database.reviews.find_one({"_id": str(review_id)})
        assert review["vote_score"] == 0
        assert await database.review_votes.count_documents({"review_id": str(review_id)}) == 0

    asyncio.run(_run_with_database(scenario))
