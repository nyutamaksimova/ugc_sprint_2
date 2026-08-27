"""Generate an equivalent deterministic UGC dataset for MongoDB or PostgreSQL."""

from __future__ import annotations

import argparse
import os
import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

FILMS = 100_000
USERS = 1_000_000


def _uuid(value: int) -> UUID:
    return UUID(int=value + 1)


def iter_records(total_records: int, seed: int):

    rng = random.Random(seed)
    start = datetime(2025, 1, 1, tzinfo=UTC)
    for number in range(total_records):
        user_id, film_id = _uuid(number % USERS), _uuid((number * 17) % FILMS)
        created_at = start + timedelta(seconds=number)
        bucket = number % 10
        if bucket < 5:
            yield (
                "ratings",
                {
                    "user_id": str(user_id),
                    "film_id": str(film_id),
                    "score": rng.randrange(11),
                    "created_at": created_at,
                },
            )
        elif bucket < 7:
            yield (
                "bookmarks",
                {"user_id": str(user_id), "film_id": str(film_id), "created_at": created_at},
            )
        elif bucket < 9:
            yield (
                "reviews",
                {
                    "id": str(_uuid(number + 20_000_000)),
                    "user_id": str(user_id),
                    "film_id": str(film_id),
                    "text": f"Review {number}",
                    "author_score": rng.randrange(11),
                    "vote_score": 0,
                    "created_at": created_at,
                },
            )
        else:
            yield (
                "review_votes",
                {
                    "user_id": str(user_id),
                    "review_id": str(_uuid((number - 1) + 20_000_000)),
                    "value": -1 if number % 2 else 1,
                    "created_at": created_at,
                },
            )


def _load_mongo(records, batch_size: int) -> int:
    from pymongo import MongoClient, ASCENDING, DESCENDING

    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true"))
    db = client["ugc_benchmark"]
    db.drop_collection("ratings")
    db.drop_collection("bookmarks")
    db.drop_collection("reviews")
    db.drop_collection("review_votes")
    count, batches = 0, {name: [] for name in ("ratings", "bookmarks", "reviews", "review_votes")}
    for kind, record in records:
        batches[kind].append(record)
        count += 1
        if len(batches[kind]) == batch_size:
            db[kind].insert_many(batches[kind], ordered=False)
            batches[kind] = []
    for kind, batch in batches.items():
        if batch:
            db[kind].insert_many(batch, ordered=False)
    db.ratings.aggregate(
        [
            {
                "$group": {
                    "_id": "$film_id",
                    "score_count": {"$sum": 1},
                    "score_sum": {"$sum": "$score"},
                    "likes_count": {"$sum": {"$cond": [{"$eq": ["$score", 10]}, 1, 0]}},
                    "dislikes_count": {"$sum": {"$cond": [{"$eq": ["$score", 0]}, 1, 0]}},
                }
            },
            {
                "$project": {
                    "film_id": "$_id",
                    "score_count": 1,
                    "score_sum": 1,
                    "likes_count": 1,
                    "dislikes_count": 1,
                }
            },
            {"$out": "rating_summaries"},
        ]
    )
    db.rating_summaries.create_index("film_id", unique=True)
    db.ratings.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.ratings.create_index([("film_id", ASCENDING)])
    db.bookmarks.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    for field in ("created_at", "author_score", "vote_score"):
        db.reviews.create_index([("film_id", ASCENDING), (field, DESCENDING), ("id", ASCENDING)])
    return count


def _load_postgres(records, batch_size: int) -> int:
    import psycopg
    from psycopg.rows import dict_row

    connection = psycopg.connect(
        os.getenv("POSTGRES_DSN", "postgresql://ugc:ugc@localhost:5434/ugc"), row_factory=dict_row
    )
    count, batch = 0, []
    with connection.cursor() as cursor:
        for kind, record in records:
            batch.append((kind, record))
            count += 1
            if len(batch) == batch_size:
                _insert_pg(cursor, batch)
                batch = []
        if batch:
            _insert_pg(cursor, batch)
        cursor.execute(
            "INSERT INTO rating_summaries (film_id, score_count, score_sum, likes_count, dislikes_count) SELECT film_id, count(*), sum(score), count(*) FILTER (WHERE score = 10), count(*) FILTER (WHERE score = 0) FROM ratings GROUP BY film_id"
        )
    connection.commit()
    connection.close()
    return count


def _insert_pg(cursor, batch):
    groups = {}
    for kind, item in batch:
        groups.setdefault(kind, []).append(item)
    for kind, rows in groups.items():
        columns = list(rows[0])
        values = [[row[column] for column in columns] for row in rows]
        cursor.executemany(
            f"INSERT INTO {kind} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})",
            values,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("mongo", "postgres"), required=True)
    parser.add_argument("--records", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=10_000)
    args = parser.parse_args()
    if args.records <= 10_000_000:
        raise SystemExit("--records must be greater than 10,000,000")
    loader = _load_mongo if args.target == "mongo" else _load_postgres
    loaded = loader(iter_records(args.records, args.seed), args.batch_size)
    print({"target": args.target, "loaded_records": loaded, "seed": args.seed})


if __name__ == "__main__":
    main()
