from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from src.core.config import settings
from src.core.security import bearer_scheme, current_user
from src.models.schemas import RatingWrite
from src.services.ratings import RatingService


def user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UUID:
    return current_user(credentials, settings.jwt_secret, settings.jwt_algorithm)


router = APIRouter(tags=["ratings"], dependencies=[Depends(user_id)])


def service(request: Request) -> RatingService:
    return RatingService(request.app.state.database, request.app.state.mongo_client)


@router.put("/films/{film_id}/ratings/me")
async def put_rating(
    film_id: UUID,
    body: RatingWrite,
    user: UUID = Depends(user_id),
    ratings: RatingService = Depends(service),
):
    return await ratings.put(user, film_id, body.score)


@router.get("/films/{film_id}/ratings/summary")
async def rating_summary(film_id: UUID, ratings: RatingService = Depends(service)):
    return await ratings.get_summary(film_id)


@router.delete("/films/{film_id}/ratings/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    film_id: UUID, user: UUID = Depends(user_id), ratings: RatingService = Depends(service)
):
    if not await ratings.delete(user, film_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
