from google.cloud.firestore_v1 import SERVER_TIMESTAMP, ArrayUnion, Increment
from app.firebase import get_firestore
from app.models.schemas import ReviewCreate, ReviewOut


def _fs():
    return get_firestore()


BADGE_RULES = [
    {"id": "quick_starter",   "min_sessions": 1},
    {"id": "verified_mentor", "min_sessions": 10},
    {"id": "grand_mentor",    "min_sessions": 20},
    {"id": "legend",          "min_sessions": 50},
]
RATING_BADGE = {"id": "top_rated", "min_rating": 4.8, "min_count": 5}


def _award_badges(profile: dict) -> list[str]:
    earned = set(profile.get("badges", []))
    new_badges = []
    sessions = profile.get("sessionsCount", 0)
    for rule in BADGE_RULES:
        if rule["id"] not in earned and sessions >= rule["min_sessions"]:
            new_badges.append(rule["id"])
    rating = profile.get("rating", 0)
    count  = profile.get("ratingCount", 0)
    if (RATING_BADGE["id"] not in earned
            and rating >= RATING_BADGE["min_rating"]
            and count  >= RATING_BADGE["min_count"]):
        new_badges.append(RATING_BADGE["id"])
    return new_badges


def _update_badges(uid: str):
    ref  = _fs().collection("users").document(uid)
    snap = ref.get()
    if snap.exists:
        new_b = _award_badges(snap.to_dict())
        if new_b:
            ref.update({"badges": ArrayUnion(new_b)})


async def submit_review(uid: str, payload: ReviewCreate) -> ReviewOut:
    # Duplicate guard
    existing = (_fs().collection("reviews")
                .where("sessionId", "==", payload.session_id)
                .where("fromUid", "==", uid)
                .limit(1).stream())
    if any(True for _ in existing):
        raise ValueError("Already reviewed this session.")

    # Participant guard
    sess_snap = _fs().collection("sessions").document(payload.session_id).get()
    if not sess_snap.exists or uid not in sess_snap.to_dict().get("participants", []):
        raise PermissionError("Not a participant of this session.")

    doc = {
        "fromUid": uid, "toUid": payload.to_uid,
        "sessionId": payload.session_id,
        "rating": payload.rating, "text": payload.text,
        "createdAt": SERVER_TIMESTAMP,
    }
    _, ref = _fs().collection("reviews").add(doc)

    # Update recipient running average
    rec_ref  = _fs().collection("users").document(payload.to_uid)
    rec_snap = rec_ref.get()
    if rec_snap.exists:
        rd  = rec_snap.to_dict()
        oc  = rd.get("ratingCount", 0)
        nc  = oc + 1
        nr  = round(((rd.get("rating", 0) * oc) + payload.rating) / nc, 2)
        rec_ref.update({"rating": nr, "ratingCount": nc, "sessionsCount": Increment(1)})
        _update_badges(payload.to_uid)

    # Increment sender sessions too
    _fs().collection("users").document(uid).update({"sessionsCount": Increment(1)})
    _update_badges(uid)

    from_snap = _fs().collection("users").document(uid).get()
    from_name = from_snap.to_dict().get("displayName", "") if from_snap.exists else ""

    return ReviewOut(
        review_id=ref.id,
        from_uid=uid, from_name=from_name,
        to_uid=payload.to_uid,
        session_id=payload.session_id,
        rating=payload.rating, text=payload.text,
        created_at="just now",
    )


async def get_reviews_for_user(uid: str) -> list[ReviewOut]:
    snaps = (_fs().collection("reviews")
             .where("toUid", "==", uid)
             .order_by("createdAt", direction="DESCENDING")
             .limit(20).stream())
    results = []
    for snap in snaps:
        d  = snap.to_dict()
        fs = _fs().collection("users").document(d["fromUid"]).get()
        fn = fs.to_dict().get("displayName", "") if fs.exists else ""
        ts = d.get("createdAt")
        results.append(ReviewOut(
            review_id=snap.id,
            from_uid=d["fromUid"], from_name=fn,
            to_uid=d["toUid"], session_id=d["sessionId"],
            rating=d["rating"], text=d["text"],
            created_at=str(ts) if ts else "",
        ))
    return results
