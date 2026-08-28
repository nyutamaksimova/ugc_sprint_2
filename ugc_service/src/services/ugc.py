import base64
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError


class UgcService:
    def __init__(self, database, mongo_client):
        self.database = database
        self.mongo_client = mongo_client

    async def _run_transaction(self, callback):
        for attempt in range(3):
            try:
                async with await self.mongo_client.start_session() as session:
                    return await session.with_transaction(callback)
            except DuplicateKeyError:
                if attempt == 2:
                    raise

    async def put_bookmark(self, user_id: UUID, film_id: UUID):
        await self.database.bookmarks.update_one(
            {"user_id": str(user_id), "film_id": str(film_id)},
            {
                "$setOnInsert": {
                    "user_id": str(user_id),
                    "film_id": str(film_id),
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    async def delete_bookmark(self, user_id: UUID, film_id: UUID) -> bool:
        return (
            await self.database.bookmarks.delete_one(
                {"user_id": str(user_id), "film_id": str(film_id)}
            )
        ).deleted_count == 1

    @staticmethod
    def _encode_cursor(sort: str, value, item_id: str) -> str:
        if isinstance(value, datetime):
            value = value.isoformat()
        payload = json.dumps({"sort": sort, "value": value, "id": item_id}).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str, sort: str):
        try:
            padding = "=" * (-len(cursor) % 4)
            payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
            if payload["sort"] != sort:
                raise ValueError
            value = payload["value"]
            if sort == "created_at":
                value = datetime.fromisoformat(value)
            elif not isinstance(value, int) or isinstance(value, bool):
                raise ValueError
            return value, payload["id"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("Invalid cursor") from error

    async def bookmarks(self, user_id: UUID, limit: int = 20, cursor: str | None = None):
        query: dict[str, object] = {"user_id": str(user_id)}
        if cursor:
            created_at, film_id = self._decode_cursor(cursor, "created_at")
            query["$or"] = [
                {"created_at": {"$lt": created_at}},
                {"created_at": created_at, "film_id": {"$gt": film_id}},
            ]
        rows = [
            item
            async for item in self.database.bookmarks.find(query, {"_id": 0})
            .sort([("created_at", DESCENDING), ("film_id", ASCENDING)])
            .limit(limit + 1)
        ]
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = items[-1]
            next_cursor = self._encode_cursor("created_at", last["created_at"], last["film_id"])
        return {"items": items, "next_cursor": next_cursor}

    async def list_reviews(
        self, film_id: UUID, sort: str = "created_at", limit: int = 20, cursor: str | None = None
    ):
        if sort not in {"created_at", "author_score", "vote_score"}:
            raise ValueError("Unsupported sort")
        query: dict[str, object] = {"film_id": str(film_id)}
        if cursor:
            value, review_id = self._decode_cursor(cursor, sort)
            query["$or"] = [{sort: {"$lt": value}}, {sort: value, "_id": {"$gt": review_id}}]
        rows = [
            review
            async for review in self.database.reviews.find(query)
            .sort([(sort, DESCENDING), ("_id", ASCENDING)])
            .limit(limit + 1)
        ]
        page = rows[:limit]
        items = [
            {key: value for key, value in review.items() if key != "_id"} | {"id": review["_id"]}
            for review in page
        ]
        next_cursor = None
        if len(rows) > limit:
            last = page[-1]
            next_cursor = self._encode_cursor(sort, last[sort], last["_id"])
        return {"items": items, "next_cursor": next_cursor}

    async def create_review(
        self, user_id: UUID, film_id: UUID, text: str, author_score: int | None
    ):
        review = {
            "_id": str(uuid4()),
            "user_id": str(user_id),
            "film_id": str(film_id),
            "text": text,
            "author_score": author_score,
            "vote_score": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await self.database.reviews.insert_one(review)
        return review

    async def update_review(self, user_id: UUID, review_id: UUID, text: str):
        return await self.database.reviews.find_one_and_update(
            {"_id": str(review_id), "user_id": str(user_id)},
            {"$set": {"text": text, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )

    async def delete_review(self, user_id: UUID, review_id: UUID) -> bool:
        review = await self.database.reviews.find_one_and_delete(
            {"_id": str(review_id), "user_id": str(user_id)}
        )
        if review:
            await self.database.review_votes.delete_many({"review_id": str(review_id)})
        return review is not None

    async def vote(self, user_id: UUID, review_id: UUID, value: int):
        return await self._run_transaction(
            lambda session: self._vote_in_transaction(session, user_id, review_id, value)
        )

    async def _vote_in_transaction(self, session, user_id: UUID, review_id: UUID, value: int):
        review = await self.database.reviews.find_one({"_id": str(review_id)}, session=session)
        if review is None:
            return None
        old = await self.database.review_votes.find_one_and_update(
            {"user_id": str(user_id), "review_id": str(review_id)},
            {"$set": {"value": value, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
            session=session,
        )
        delta = value - (old["value"] if old else 0)
        return await self.database.reviews.find_one_and_update(
            {"_id": str(review_id)},
            {"$inc": {"vote_score": delta}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

    async def delete_vote(self, user_id: UUID, review_id: UUID) -> bool:
        return await self._run_transaction(
            lambda session: self._delete_vote_in_transaction(session, user_id, review_id)
        )

    async def _delete_vote_in_transaction(self, session, user_id: UUID, review_id: UUID) -> bool:
        review = await self.database.reviews.find_one({"_id": str(review_id)}, session=session)
        if review is None:
            return False
        old = await self.database.review_votes.find_one_and_delete(
            {"user_id": str(user_id), "review_id": str(review_id)}, session=session
        )
        if old:
            await self.database.reviews.update_one(
                {"_id": str(review_id)},
                {"$inc": {"vote_score": -old["value"]}},
                session=session,
            )
        return old is not None
