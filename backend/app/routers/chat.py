from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.schemas import ChatMessage, MessageOut
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/send", response_model=MessageOut, status_code=201)
async def send(payload: ChatMessage, user=Depends(get_current_user)):
    return await chat_service.send_message(user["uid"], payload)

@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def messages(chat_id: str, limit: int = 50, user=Depends(get_current_user)):
    return await chat_service.get_messages(user["uid"], chat_id, limit)

@router.get("/id/{other_uid}", response_model=dict)
async def chat_id(other_uid: str, user=Depends(get_current_user)):
    return {"chat_id": chat_service.get_chat_id_for(user["uid"], other_uid)}
@router.get("/my")
async def my_chats(user=Depends(get_current_user)):
    return await chat_service.get_user_chats(user["uid"])
@router.post("/{chat_id}/read")
async def read(chat_id: str, user=Depends(get_current_user)):
    await chat_service.mark_read(chat_id, user["uid"])
    return {"success": True}