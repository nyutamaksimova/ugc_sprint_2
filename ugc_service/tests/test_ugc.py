import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from src.services.ugc import UgcService


def test_ugc_service_keeps_mongo_client():
    client = object()
    service = UgcService(database=object(), mongo_client=client)

    assert service.mongo_client is client


def test_vote_for_missing_review_does_not_create_vote():
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(session)

    session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock(start_session=AsyncMock(return_value=session))
    reviews = SimpleNamespace(
        find_one=AsyncMock(return_value=None), find_one_and_update=AsyncMock(return_value=None)
    )
    votes = SimpleNamespace(find_one_and_update=AsyncMock(return_value=None))
    service = UgcService(SimpleNamespace(reviews=reviews, review_votes=votes), client)

    assert asyncio.run(service.vote(uuid4(), uuid4(), 1)) is None

    reviews.find_one.assert_awaited_once()
    votes.find_one_and_update.assert_not_awaited()


def test_vote_uses_one_transaction_session_for_vote_and_review():
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(session)

    session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock(start_session=AsyncMock(return_value=session))
    reviews = SimpleNamespace(
        find_one=AsyncMock(return_value={"_id": "review"}),
        find_one_and_update=AsyncMock(return_value={"_id": "review", "vote_score": 1}),
    )
    votes = SimpleNamespace(find_one_and_update=AsyncMock(return_value=None))
    service = UgcService(SimpleNamespace(reviews=reviews, review_votes=votes), client)

    assert asyncio.run(service.vote(uuid4(), uuid4(), 1))["vote_score"] == 1

    session.with_transaction.assert_awaited_once()
    assert reviews.find_one.await_args.kwargs["session"] is session
    assert votes.find_one_and_update.await_args.kwargs["session"] is session
    assert reviews.find_one_and_update.await_args.kwargs["session"] is session


def test_delete_vote_uses_one_transaction_session_for_vote_and_review():
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(session)

    session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock(start_session=AsyncMock(return_value=session))
    reviews = SimpleNamespace(
        find_one=AsyncMock(return_value={"_id": "review"}), update_one=AsyncMock()
    )
    votes = SimpleNamespace(find_one_and_delete=AsyncMock(return_value={"value": 1}))
    service = UgcService(SimpleNamespace(reviews=reviews, review_votes=votes), client)

    assert asyncio.run(service.delete_vote(uuid4(), uuid4())) is True

    session.with_transaction.assert_awaited_once()
    assert reviews.find_one.await_args.kwargs["session"] is session
    assert votes.find_one_and_delete.await_args.kwargs["session"] is session
    assert reviews.update_one.await_args.kwargs["session"] is session


def test_transaction_retries_duplicate_key_conflict():
    failed_session = MagicMock()
    failed_session.__aenter__ = AsyncMock(return_value=failed_session)
    failed_session.__aexit__ = AsyncMock(return_value=False)
    failed_session.with_transaction = AsyncMock(side_effect=DuplicateKeyError("duplicate key"))
    successful_session = MagicMock()
    successful_session.__aenter__ = AsyncMock(return_value=successful_session)
    successful_session.__aexit__ = AsyncMock(return_value=False)

    async def with_transaction(callback):
        return await callback(successful_session)

    successful_session.with_transaction = AsyncMock(side_effect=with_transaction)
    client = MagicMock(start_session=AsyncMock(side_effect=[failed_session, successful_session]))
    service = UgcService(database=object(), mongo_client=client)

    async def callback(_):
        return "completed"

    assert asyncio.run(service._run_transaction(callback)) == "completed"
    assert client.start_session.await_count == 2


def test_list_reviews_uses_stable_author_score_sort():
    class Cursor:
        def __init__(self):
            self.sort_arguments = None

        def sort(self, arguments):
            self.sort_arguments = arguments
            return self

        def limit(self, _):
            return self

        def __aiter__(self):
            async def items():
                if False:
                    yield None

            return items()

    cursor = Cursor()
    reviews = SimpleNamespace(find=MagicMock(return_value=cursor))
    service = UgcService(SimpleNamespace(reviews=reviews), mongo_client=object())

    assert asyncio.run(service.list_reviews(uuid4(), sort="author_score"))["items"] == []
    assert cursor.sort_arguments == [("author_score", -1), ("_id", 1)]


def test_bookmarks_returns_bounded_page_with_cursor():
    now = datetime.now(timezone.utc)

    class Cursor:
        def __init__(self, items):
            self.items = items
            self.limit_value = None

        def sort(self, _):
            return self

        def limit(self, value):
            self.limit_value = value
            return self

        def __aiter__(self):
            async def items():
                for item in self.items:
                    yield item

            return items()

    cursor = Cursor(
        [
            {"film_id": "first", "created_at": now},
            {"film_id": "second", "created_at": now},
        ]
    )
    bookmarks = SimpleNamespace(find=MagicMock(return_value=cursor))
    service = UgcService(SimpleNamespace(bookmarks=bookmarks), mongo_client=object())

    page = asyncio.run(service.bookmarks(uuid4(), limit=1))

    assert cursor.limit_value == 2
    assert page["items"] == [{"film_id": "first", "created_at": now}]
    assert page["next_cursor"]
