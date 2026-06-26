from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.schemas import SessionCreate, SessionUpdate, SessionOut
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("/", response_model=SessionOut, status_code=201)
async def create(payload: SessionCreate, user=Depends(get_current_user)):
    return await session_service.create_session(user["uid"], payload)

@router.get("/", response_model=list[SessionOut])
async def list_sessions(user=Depends(get_current_user)):
    return await session_service.get_my_sessions(user["uid"])

@router.patch("/{session_id}", response_model=SessionOut)
async def update(session_id: str, payload: SessionUpdate, user=Depends(get_current_user)):
    result = await session_service.update_session(user["uid"], session_id, payload)
    if not result:
        raise HTTPException(404, "Session not found or not a participant")
    return result
