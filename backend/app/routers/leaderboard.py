from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.schemas import LeaderboardEntry
from app.services import leaderboard_service

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/sessions", response_model=list[LeaderboardEntry])
async def by_sessions(limit: int = 10, user=Depends(get_current_user)):
    return await leaderboard_service.get_leaderboard_by_sessions(limit)

@router.get("/rating", response_model=list[LeaderboardEntry])
async def by_rating(limit: int = 10, user=Depends(get_current_user)):
    return await leaderboard_service.get_leaderboard_by_rating(limit)

@router.get("/stats", response_model=dict)
async def stats(user=Depends(get_current_user)):
    return await leaderboard_service.get_community_stats()
