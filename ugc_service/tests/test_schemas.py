import pytest
from pydantic import ValidationError

from src.models.schemas import RatingWrite, VoteWrite


def test_rating_accepts_bounds_and_rejects_invalid_score():
    assert RatingWrite(score=10).score == 10
    with pytest.raises(ValidationError):
        RatingWrite(score=11)


def test_review_vote_accepts_only_plus_or_minus_one():
    assert VoteWrite(value=-1).value == -1
    with pytest.raises(ValidationError):
        VoteWrite(value=0)
