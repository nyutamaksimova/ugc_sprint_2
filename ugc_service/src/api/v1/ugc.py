from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.v1.ratings import user_id
from src.models.schemas import ReviewCreate, ReviewUpdate, VoteWrite
from src.services.ugc import UgcService

router = APIRouter(tags=["ugc"])


def service(request: Request):
    return UgcService(request.app.state.database)


@router.put("/users/me/bookmarks/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
async def put_bookmark(
    film_id: UUID, user: UUID = Depends(user_id), ugc: UgcService = Depends(service)
):
    await ugc.put_bookmark(user, film_id)


@router.delete("/users/me/bookmarks/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    film_id: UUID, user: UUID = Depends(user_id), ugc: UgcService = Depends(service)
):
    if not await ugc.delete_bookmark(user, film_id):
        raise HTTPException(404, "Bookmark not found")


@router.get("/users/me/bookmarks")
async def bookmarks(user: UUID = Depends(user_id), ugc: UgcService = Depends(service)):
    return await ugc.bookmarks(user)


@router.post("/films/{film_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(
    film_id: UUID,
    body: ReviewCreate,
    user: UUID = Depends(user_id),
    ugc: UgcService = Depends(service),
):
    return await ugc.create_review(user, film_id, body.text, body.author_score)


@router.get("/films/{film_id}/reviews")
async def reviews(
    film_id: UUID, sort: str = "created_at", limit: int = 20, ugc: UgcService = Depends(service)
):
    try:
        return await ugc.list_reviews(film_id, sort, min(limit, 100))
    except ValueError:
        raise HTTPException(422, "Unsupported sort")


@router.patch("/reviews/{review_id}")
async def patch_review(
    review_id: UUID,
    body: ReviewUpdate,
    user: UUID = Depends(user_id),
    ugc: UgcService = Depends(service),
):
    result = await ugc.update_review(user, review_id, body.text)
    if not result:
        raise HTTPException(404, "Review not found")
    return result


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID, user: UUID = Depends(user_id), ugc: UgcService = Depends(service)
):
    if not await ugc.delete_review(user, review_id):
        raise HTTPException(404, "Review not found")


@router.put("/reviews/{review_id}/votes/me")
async def vote(
    review_id: UUID,
    body: VoteWrite,
    user: UUID = Depends(user_id),
    ugc: UgcService = Depends(service),
):
    result = await ugc.vote(user, review_id, body.value)
    if not result:
        raise HTTPException(404, "Review not found")
    return result


@router.delete("/reviews/{review_id}/votes/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vote(
    review_id: UUID, user: UUID = Depends(user_id), ugc: UgcService = Depends(service)
):
    if not await ugc.delete_vote(user, review_id):
        raise HTTPException(404, "Vote not found")
