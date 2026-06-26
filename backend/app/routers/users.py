from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.schemas import UserCreate, UserUpdate, UserProfile
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserProfile, status_code=201)
async def create_profile(payload: UserCreate, user=Depends(get_current_user)):
    existing = await user_service.get_user_profile(user["uid"])
    if existing:
        raise HTTPException(409, "Profile already exists")
    return await user_service.create_user_profile(user["uid"], user.get("email",""), payload)

@router.get("/me", response_model=UserProfile)
async def get_my_profile(user=Depends(get_current_user)):
    prof = await user_service.get_user_profile(user["uid"])
    if not prof:
        raise HTTPException(404, "Profile not found")
    return prof

@router.put("/me", response_model=UserProfile)
async def update_profile(payload: UserUpdate, user=Depends(get_current_user)):
    return await user_service.update_user_profile(user["uid"], payload)

@router.get("/{uid}", response_model=UserProfile)
async def get_profile(uid: str, user=Depends(get_current_user)):
    prof = await user_service.get_user_profile(uid)
    if not prof:
        raise HTTPException(404, "User not found")
    return prof

@router.post("/me/skills/teach", response_model=UserProfile)
async def add_teach(skill: dict, user=Depends(get_current_user)):
    return await user_service.add_teach_skill(user["uid"], skill)

@router.delete("/me/skills/teach/{skill_name}", response_model=UserProfile)
async def remove_teach(skill_name: str, user=Depends(get_current_user)):
    return await user_service.remove_teach_skill(user["uid"], skill_name)

@router.post("/me/skills/learn", response_model=UserProfile)
async def add_learn(body: dict, user=Depends(get_current_user)):
    return await user_service.add_learn_skill(user["uid"], body.get("skill",""))

@router.delete("/me/skills/learn/{skill}", response_model=UserProfile)
async def remove_learn(skill: str, user=Depends(get_current_user)):
    return await user_service.remove_learn_skill(user["uid"], skill)

@router.get("/", response_model=list[UserProfile])
async def list_users(user=Depends(get_current_user)):
    return await user_service.get_all_users()
