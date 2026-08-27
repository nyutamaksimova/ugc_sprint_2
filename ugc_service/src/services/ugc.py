from datetime import datetime, timezone
from uuid import UUID, uuid4

from pymongo import ReturnDocument


class UgcService:
    def __init__(self, database):
        self.database = database

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

    async def bookmarks(self, user_id: UUID):
        return [
            {"film_id": item["film_id"], "created_at": item["created_at"]}
            async for item in self.database.bookmarks.find(
                {"user_id": str(user_id)}, {"_id": 0}
            ).sort("created_at", -1)
        ]

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

    async def list_reviews(self, film_id: UUID, sort: str = "created_at", limit: int = 20):
        if sort not in {"created_at", "author_score", "vote_score"}:
            raise ValueError("Unsupported sort")
        return [
            {key: value for key, value in review.items() if key != "_id"} | {"id": review["_id"]}
            async for review in self.database.reviews.find({"film_id": str(film_id)})
            .sort(sort, -1)
            .limit(limit)
        ]

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
        old = await self.database.review_votes.find_one_and_update(
            {"user_id": str(user_id), "review_id": str(review_id)},
            {"$set": {"value": value, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        delta = value - (old["value"] if old else 0)
        return await self.database.reviews.find_one_and_update(
            {"_id": str(review_id)},
            {"$inc": {"vote_score": delta}},
            return_document=ReturnDocument.AFTER,
        )

    async def delete_vote(self, user_id: UUID, review_id: UUID) -> bool:
        old = await self.database.review_votes.find_one_and_delete(
            {"user_id": str(user_id), "review_id": str(review_id)}
        )
        if old:
            await self.database.reviews.update_one(
                {"_id": str(review_id)}, {"$inc": {"vote_score": -old["value"]}}
            )
        return old is not None
