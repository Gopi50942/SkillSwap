from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.schemas import ReviewCreate, ReviewOut
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewOut, status_code=201)
async def submit(payload: ReviewCreate, user=Depends(get_current_user)):
    try:
        return await review_service.submit_review(user["uid"], payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))

@router.get("/{uid}", response_model=list[ReviewOut])
async def get_reviews(uid: str, user=Depends(get_current_user)):
    return await review_service.get_reviews_for_user(uid)
