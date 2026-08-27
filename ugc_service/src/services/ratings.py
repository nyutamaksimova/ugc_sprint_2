from datetime import datetime, timezone
from uuid import UUID

from pymongo import ReturnDocument


def _delta(score: int, factor: int = 1) -> dict[str, int]:
    return {
        "score_count": factor,
        "score_sum": score * factor,
        "likes_count": factor if score == 10 else 0,
        "dislikes_count": factor if score == 0 else 0,
    }


class RatingService:
    def __init__(self, database):
        self.database = database

    async def put(self, user_id: UUID, film_id: UUID, score: int) -> dict:
        now = datetime.now(timezone.utc)
        previous = await self.database.ratings.find_one_and_update(
            {"user_id": str(user_id), "film_id": str(film_id)},
            {"$set": {"score": score, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        change = _delta(score)
        if previous:
            for key, value in _delta(previous["score"], -1).items():
                change[key] += value
        summary = await self.database.rating_summaries.find_one_and_update(
            {"film_id": str(film_id)},
            {"$inc": change, "$setOnInsert": {"film_id": str(film_id)}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self._present(summary)

    async def get_summary(self, film_id: UUID) -> dict:
        summary = await self.database.rating_summaries.find_one({"film_id": str(film_id)})
        return self._present(
            summary or {"score_count": 0, "score_sum": 0, "likes_count": 0, "dislikes_count": 0}
        )

    async def delete(self, user_id: UUID, film_id: UUID) -> bool:
        rating = await self.database.ratings.find_one_and_delete(
            {"user_id": str(user_id), "film_id": str(film_id)}
        )
        if rating is None:
            return False
        await self.database.rating_summaries.update_one(
            {"film_id": str(film_id)}, {"$inc": _delta(rating["score"], -1)}
        )
        return True

    @staticmethod
    def _present(summary: dict) -> dict:
        count = summary["score_count"]
        return {
            "score_count": count,
            "likes_count": summary["likes_count"],
            "dislikes_count": summary["dislikes_count"],
            "average": (summary["score_sum"] / count if count else 0.0),
        }
