from pymongo import ASCENDING, DESCENDING


async def ensure_indexes(database) -> None:
    await database.ratings.create_index(
        [("user_id", ASCENDING), ("film_id", ASCENDING)], unique=True, name="rating_user_film"
    )
    await database.ratings.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], name="ratings_user_created"
    )
    await database.ratings.create_index([("film_id", ASCENDING)], name="ratings_film")
    await database.rating_summaries.create_index("film_id", unique=True, name="summary_film")
    await database.bookmarks.create_index(
        [("user_id", ASCENDING), ("film_id", ASCENDING)], unique=True, name="bookmark_user_film"
    )
    await database.bookmarks.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], name="bookmarks_user_created"
    )
    await database.bookmarks.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING), ("film_id", ASCENDING)],
        name="bookmarks_user_created_film",
    )
    await database.reviews.create_index(
        [("film_id", ASCENDING), ("created_at", DESCENDING), ("_id", ASCENDING)],
        name="reviews_film_created",
    )
    await database.reviews.create_index(
        [("film_id", ASCENDING), ("vote_score", DESCENDING), ("_id", ASCENDING)],
        name="reviews_film_votes",
    )
    await database.reviews.create_index(
        [("film_id", ASCENDING), ("author_score", DESCENDING), ("_id", ASCENDING)],
        name="reviews_film_author_score",
    )
    await database.review_votes.create_index(
        [("user_id", ASCENDING), ("review_id", ASCENDING)],
        unique=True,
        name="review_vote_user_review",
    )
