"""
Matching engine — scores candidates by skill overlap + rating.
score = (teach_overlap*0.5 + learn_overlap*0.4 + rating_boost*0.1)
        / max(len(my_learn),1) * 100
"""
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from app.firebase import get_firestore
from app.models.schemas import SuggestedMatch, MatchOut, SkillTeach
from app.config import get_settings
from app.services import chat_service


def _fs():
    return get_firestore()


def _calc_score(me: dict, other: dict) -> int:
    my_teach  = {(s.get("skill") or s).lower() for s in me.get("skillsTeach", [])}
    my_learn  = {s.lower() for s in me.get("skillsLearn", [])}
    th_teach  = {(s.get("skill") or s).lower() for s in other.get("skillsTeach", [])}
    th_learn  = {s.lower() for s in other.get("skillsLearn", [])}
    teach_ov  = len(th_teach & my_learn)
    learn_ov  = len(my_teach & th_learn)
    r_boost   = (other.get("rating") or 0) / 5.0
    denom     = max(len(my_learn), 1)
    raw       = (teach_ov * 0.5 + learn_ov * 0.4 + r_boost * 0.1) / denom
    return min(int(raw * 100) + 5, 99)


def _to_skill_list(raw: list) -> list[SkillTeach]:
    result = []
    for s in raw:
        if isinstance(s, dict):
            result.append(SkillTeach(skill=s.get("skill",""), level=s.get("level","Intermediate")))
        else:
            result.append(SkillTeach(skill=str(s), level="Intermediate"))
    return result


async def get_suggested_matches(uid: str) -> list[SuggestedMatch]:
    me_snap = _fs().collection("users").document(uid).get()
    if not me_snap.exists:
        return []
    me = me_snap.to_dict()
    my_learn = [
    (s.get("skill") if isinstance(s, dict) else s).lower()
    for s in me.get("skillsLearn", [])
]

    if my_learn:
        snaps = list(_fs().collection("users")
                     .where("skillsLearn", "array_contains_any", my_learn[:10])
                     .stream())
        if not snaps:
            snaps = list(_fs().collection("users").stream())
    else:
        snaps = list(_fs().collection("users")
                     .order_by("sessionsCount", direction="DESCENDING")
                     .limit(get_settings().match_limit).stream())

    results = []
    for snap in snaps:
        if snap.id == uid:
            continue
        other = snap.to_dict()
        score = _calc_score(me, other)
        results.append(SuggestedMatch(
            uid=snap.id,
            display_name=other.get("displayName", ""),
            college=other.get("college", ""),
            rating=other.get("rating", 0.0),
            rating_count=other.get("ratingCount", 0),
            sessions_count=other.get("sessionsCount", 0),
            skills_teach=_to_skill_list(other.get("skillsTeach", [])),
            skills_learn=other.get("skillsLearn", []),
            match_pct=score,
        ))
    results.sort(key=lambda x: x.match_pct, reverse=True)
    return results[:get_settings().match_limit]


async def create_match(uid1: str, uid2: str) -> str:

    if uid1 == uid2:
        raise ValueError("You cannot connect with yourself.")

    match_id = "__".join(sorted([uid1, uid2]))
    ref = _fs().collection("matches").document(match_id)

    # Prevent duplicate requests
    if ref.get().exists:
        return match_id

    me_snap = _fs().collection("users").document(uid1).get()
    other_snap = _fs().collection("users").document(uid2).get()

    score = 0

    if me_snap.exists and other_snap.exists:
        score = _calc_score(
            me_snap.to_dict(),
            other_snap.to_dict()
        )

    ref.set({

        "participants": [uid1, uid2],

        # NEW
        "senderUid": uid1,
        "receiverUid": uid2,

        "score": score,

        "status": "pending",

        "createdAt": SERVER_TIMESTAMP,

        # NEW
        "acceptedAt": None,

        "chatId": None

    })

    return match_id


async def get_my_matches(uid: str) -> list[MatchOut]:
    snaps = (_fs().collection("matches")
             .where("participants", "array_contains", uid)
             .stream())
    results = []
    for snap in snaps:
        data = snap.to_dict()
        partner_uid = next(p for p in data["participants"] if p != uid)
        ps = _fs().collection("users").document(partner_uid).get()
        p = ps.to_dict() if ps.exists else {}
        results.append(MatchOut(
            match_id=snap.id,
            partner_uid=partner_uid,
            partner_name=p.get("displayName", ""),
            partner_college=p.get("college", ""),
            partner_rating=p.get("rating", 0.0),
            partner_sessions=p.get("sessionsCount", 0),
            partner_skills_teach=_to_skill_list(p.get("skillsTeach", [])),
            partner_skills_learn=p.get("skillsLearn", []),
            match_pct=data.get("score", 0),
            status=data.get("status", "pending"),
            sender_uid=data.get("senderUid", ""),   # ADD THIS LINE
))
    results.sort(key=lambda x: x.match_pct, reverse=True)
    return results


async def update_match_status(match_id: str, uid: str, status: str):
    ref = _fs().collection("matches").document(match_id)
    snap = ref.get()
    if not snap.exists:
        return False
    data = snap.to_dict()
    if uid not in data.get("participants", []):
        return False
    update_data = {"status": status}
    if status == "accepted":
        uid1 = data["participants"][0]
        uid2 = data["participants"][1]
        u1 = _fs().collection("users").document(uid1).get().to_dict() or {}
        u2 = _fs().collection("users").document(uid2).get().to_dict() or {}
        chat_id = await chat_service.create_chat(
            uid1, uid2,
            u1.get("displayName", "User"),
            u2.get("displayName", "User")
        )
        update_data["acceptedAt"] = SERVER_TIMESTAMP
        update_data["chatId"] = chat_id
    ref.update(update_data)
    return True