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
async def list_users(user=Depends(get_current_user), search: str = ""):
    users_list = await user_service.get_all_users()
    if search:
        q = search.lower()
        users_list = [u for u in users_list if
            q in (u.display_name or "").lower() or
            q in (u.college or "").lower() or
            any(q in (s.skill if hasattr(s,"skill") else str(s)).lower() for s in u.skills_teach) or
            any(q in str(s).lower() for s in u.skills_learn)]
    return users_list

@router.get("/feed/activity")
async def get_activity_feed(user=Depends(get_current_user)):
    """Get recent platform activity feed"""
    from app.firebase import get_firestore
    from google.cloud.firestore_v1 import Query
    db = get_firestore()
    results = []
    try:
        snaps = list(db.collection("users").order_by("createdAt", direction=Query.DESCENDING).limit(5).stream())
        for snap in snaps:
            if snap.id == user["uid"]: continue
            d = snap.to_dict()
            results.append({"icon":"🎉","text":f"{d.get('displayName','Someone')} joined SkillSwap","time":""})
    except: pass
    try:
        snaps = list(db.collection("matches").where("status","==","accepted").limit(5).stream())
        for snap in snaps:
            d = snap.to_dict()
            parts = d.get("participants",[])
            if len(parts)>=2:
                u1 = db.collection("users").document(parts[0]).get()
                u2 = db.collection("users").document(parts[1]).get()
                n1 = u1.to_dict().get("displayName","Someone") if u1.exists else "Someone"
                n2 = u2.to_dict().get("displayName","Someone") if u2.exists else "Someone"
                results.append({"icon":"🤝","text":f"{n1} and {n2} connected","time":""})
    except: pass
    return results[:8]