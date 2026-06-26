from google.cloud.firestore_v1 import SERVER_TIMESTAMP, ArrayUnion
from app.firebase import get_firestore
from app.models.schemas import UserCreate, UserUpdate, UserProfile, SkillTeach


def _fs():
    return get_firestore()


def _to_profile(uid: str, d: dict) -> UserProfile:
    teach_raw = d.get("skillsTeach", [])
    teach = []
    for s in teach_raw:
        if isinstance(s, dict):
            teach.append(SkillTeach(skill=s.get("skill",""), level=s.get("level","Intermediate")))
        else:
            teach.append(SkillTeach(skill=str(s), level="Intermediate"))
    return UserProfile(
        uid=uid,
        display_name=d.get("displayName",""),
        email=d.get("email",""),
        college=d.get("college",""),
        bio=d.get("bio",""),
        photo_url=d.get("photoURL"),
        skills_teach=teach,
        skills_learn=d.get("skillsLearn",[]),
        rating=d.get("rating",0.0),
        rating_count=d.get("ratingCount",0),
        sessions_count=d.get("sessionsCount",0),
        badges=d.get("badges",[]),
    )


async def create_user_profile(uid: str, email: str, payload: UserCreate) -> UserProfile:
    doc = {
        "displayName": payload.display_name, "email": email,
        "college": payload.college, "bio": payload.bio, "photoURL": None,
        "skillsTeach": [], "skillsLearn": [],
        "rating": 0.0, "ratingCount": 0, "sessionsCount": 0,
        "badges": [], "createdAt": SERVER_TIMESTAMP,
    }
    _fs().collection("users").document(uid).set(doc)
    return _to_profile(uid, doc)


async def get_user_profile(uid: str) -> UserProfile | None:
    snap = _fs().collection("users").document(uid).get()
    if not snap.exists:
        return None
    return _to_profile(uid, snap.to_dict())


async def update_user_profile(uid: str, payload: UserUpdate) -> UserProfile:
    upd = {}
    if payload.display_name is not None: upd["displayName"] = payload.display_name
    if payload.college is not None:      upd["college"] = payload.college
    if payload.bio is not None:          upd["bio"] = payload.bio
    if payload.skills_teach is not None: upd["skillsTeach"] = [s.model_dump() for s in payload.skills_teach]
    if payload.skills_learn is not None: upd["skillsLearn"] = payload.skills_learn
    if upd:
        upd["updatedAt"] = SERVER_TIMESTAMP
        _fs().collection("users").document(uid).update(upd)
    snap = _fs().collection("users").document(uid).get()
    return _to_profile(uid, snap.to_dict())


async def add_teach_skill(uid: str, skill: dict) -> UserProfile:
    _fs().collection("users").document(uid).update({"skillsTeach": ArrayUnion([skill])})
    return await get_user_profile(uid)


async def remove_teach_skill(uid: str, skill_name: str) -> UserProfile:
    snap = _fs().collection("users").document(uid).get()
    skills = [s for s in snap.to_dict().get("skillsTeach", []) if s.get("skill") != skill_name]
    _fs().collection("users").document(uid).update({"skillsTeach": skills})
    return await get_user_profile(uid)


async def add_learn_skill(uid: str, skill: str) -> UserProfile:
    _fs().collection("users").document(uid).update({"skillsLearn": ArrayUnion([skill])})
    return await get_user_profile(uid)


async def remove_learn_skill(uid: str, skill: str) -> UserProfile:
    snap = _fs().collection("users").document(uid).get()
    skills = [s for s in snap.to_dict().get("skillsLearn", []) if s != skill]
    _fs().collection("users").document(uid).update({"skillsLearn": skills})
    return await get_user_profile(uid)


async def get_all_users() -> list[UserProfile]:
    return [_to_profile(s.id, s.to_dict()) for s in _fs().collection("users").stream()]
