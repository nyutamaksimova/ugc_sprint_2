"""Read benchmark for the five documented UGC scenarios."""

from __future__ import annotations
import argparse, json, math, os, statistics, time


def summarize_latencies(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)

    def percentile(value: int) -> float:
        return float(ordered[math.ceil(len(ordered) * value / 100) - 1])

    return {
        "count": len(samples),
        "mean_ms": round(statistics.fmean(samples), 3),
        "p50_ms": percentile(50),
        "p95_ms": percentile(95),
        "p99_ms": percentile(99),
    }


def _time(operation, iterations):
    samples = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return summarize_latencies(samples)


def benchmark_mongo(iterations):
    from pymongo import MongoClient

    db = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true"))[
        "ugc_benchmark"
    ]
    user, film = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001"
    return {
        "ratings_by_user": _time(
            lambda: list(db.ratings.find({"user_id": user}).sort("created_at", -1).limit(20)),
            iterations,
        ),
        "rating_summary": _time(
            lambda: db.rating_summaries.find_one({"film_id": film}), iterations
        ),
        "bookmarks_by_user": _time(
            lambda: list(db.bookmarks.find({"user_id": user}).sort("created_at", -1).limit(20)),
            iterations,
        ),
        "reviews_by_film": _time(
            lambda: list(db.reviews.find({"film_id": film}).sort("vote_score", -1).limit(20)),
            iterations,
        ),
    }


def postgres_queries() -> dict[str, str]:
    return {
        "ratings_by_user": "SELECT film_id, score FROM ratings WHERE user_id = %s ORDER BY created_at DESC LIMIT 20",
        "rating_summary": "SELECT score_count, score_sum, likes_count, dislikes_count FROM rating_summaries WHERE film_id = %s",
        "bookmarks_by_user": "SELECT film_id FROM bookmarks WHERE user_id = %s ORDER BY created_at DESC LIMIT 20",
        "reviews_by_film": "SELECT id, text FROM reviews WHERE film_id = %s ORDER BY vote_score DESC, id ASC LIMIT 20",
    }


def benchmark_postgres(iterations):
    import psycopg

    connection = psycopg.connect(
        os.getenv("POSTGRES_DSN", "postgresql://ugc:ugc@localhost:5434/ugc")
    )
    user, film = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001"
    values = {
        "ratings_by_user": user,
        "rating_summary": film,
        "bookmarks_by_user": user,
        "reviews_by_film": film,
    }
    with connection.cursor() as cursor:
        result = {
            name: _time(
                lambda q=query, v=values[name]: (cursor.execute(q, (v,)), cursor.fetchall()),
                iterations,
            )
            for name, query in postgres_queries().items()
        }
    connection.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("mongo", "postgres"), required=True)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--output", default="results.json")
    args = parser.parse_args()
    runner = benchmark_mongo if args.target == "mongo" else benchmark_postgres
    results = runner(args.iterations)
    results["target"] = args.target
    results["cache_condition"] = "warm"
    json.dump(results, open(args.output, "w"), indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
