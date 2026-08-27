from typing import Literal

from pydantic import BaseModel, Field


class RatingWrite(BaseModel):
    score: int = Field(ge=0, le=10)


class VoteWrite(BaseModel):
    value: Literal[-1, 1]


class BookmarkItem(BaseModel):
    film_id: str


class ReviewCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    author_score: int | None = Field(default=None, ge=0, le=10)


class ReviewUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
