import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.services.ratings import RatingService


def test_rating_service_keeps_mongo_client():
    client = object()
    service = RatingService(database=object(), mongo_client=client)

    assert service.mongo_client is client


def test_summary_presentation_calculates_average_and_reaction_counts():
    result = RatingService._present(
        {"score_count": 2, "score_sum": 10, "likes_count": 1, "dislikes_count": 0}
    )

    assert result == {"score_count": 2, "likes_count": 1, "dislikes_count": 0, "average": 5.0}


def test_put_uses_one_transaction_session_for_rating_and_summary():
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(session)

    session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock()
    client.start_session = AsyncMock(return_value=session)
    ratings = SimpleNamespace(find_one_and_update=AsyncMock(return_value=None))
    summaries = SimpleNamespace(
        find_one_and_update=AsyncMock(
            return_value={"score_count": 1, "score_sum": 10, "likes_count": 1, "dislikes_count": 0}
        )
    )
    service = RatingService(SimpleNamespace(ratings=ratings, rating_summaries=summaries), client)

    asyncio.run(service.put(uuid4(), uuid4(), 10))

    session.with_transaction.assert_awaited_once()
    assert ratings.find_one_and_update.await_args.kwargs["session"] is session
    assert summaries.find_one_and_update.await_args.kwargs["session"] is session


def test_delete_uses_one_transaction_session_for_rating_and_summary():
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(session)

    session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock()
    client.start_session = AsyncMock(return_value=session)
    ratings = SimpleNamespace(find_one_and_delete=AsyncMock(return_value={"score": 10}))
    summaries = SimpleNamespace(update_one=AsyncMock())
    service = RatingService(SimpleNamespace(ratings=ratings, rating_summaries=summaries), client)

    assert asyncio.run(service.delete(uuid4(), uuid4())) is True

    session.with_transaction.assert_awaited_once()
    assert ratings.find_one_and_delete.await_args.kwargs["session"] is session
    assert summaries.update_one.await_args.kwargs["session"] is session
