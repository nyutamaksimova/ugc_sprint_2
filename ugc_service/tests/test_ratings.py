from src.services.ratings import RatingService


def test_summary_presentation_calculates_average_and_reaction_counts():
    result = RatingService._present(
        {"score_count": 2, "score_sum": 10, "likes_count": 1, "dislikes_count": 0}
    )

    assert result == {"score_count": 2, "likes_count": 1, "dislikes_count": 0, "average": 5.0}
