from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.schemas import MatchCreate, MatchOut, SuggestedMatch
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("/suggested", response_model=list[SuggestedMatch])
async def suggested(user=Depends(get_current_user)):
    return await match_service.get_suggested_matches(user["uid"])

@router.get("/", response_model=list[MatchOut])
async def my_matches(user=Depends(get_current_user)):
    return await match_service.get_my_matches(user["uid"])

@router.post("/", response_model=dict, status_code=201)
async def connect(payload: MatchCreate, user=Depends(get_current_user)):
    if payload.target_uid == user["uid"]:
        raise HTTPException(400, "Cannot match with yourself")
    match_id = await match_service.create_match(user["uid"], payload.target_uid)
    return {"match_id": match_id, "message": "Match created"}

@router.patch("/{match_id}/status", response_model=dict)
async def update_status(match_id: str, body: dict, user=Depends(get_current_user)):
    new_status = body.get("status")
    if new_status not in ("pending", "active", "completed","accepted", "rejected"):
        raise HTTPException(400, "Invalid status")
    ok = await match_service.update_match_status(match_id, user["uid"], new_status)
    if not ok:
        raise HTTPException(404, "Match not found or not a participant")
    return {"message": f"Match status updated to {new_status}"}
