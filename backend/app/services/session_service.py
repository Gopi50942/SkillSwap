from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from app.firebase import get_firestore
from app.models.schemas import SessionCreate, SessionUpdate, SessionOut


def _fs():
    return get_firestore()


def _to_out(sid: str, data: dict, uid: str, partner_name: str) -> SessionOut:
    partner_uid = next((p for p in data.get("participants", []) if p != uid), "")
    return SessionOut(
        session_id=sid,
        partner_uid=partner_uid,
        partner_name=partner_name,
        topic=data.get("topic", ""),
        date_time=data.get("dateTime", ""),
        duration=data.get("duration", "60 minutes"),
        meet_link=data.get("meetLink"),
        status=data.get("status", "upcoming"),
    )


async def create_session(uid: str, payload: SessionCreate) -> SessionOut:
    doc = {
        "participants": [uid, payload.partner_uid],
        "topic": payload.topic,
        "dateTime": payload.date_time.isoformat(),
        "duration": payload.duration,
        "meetLink": payload.meet_link,
        "status": "upcoming",
        "createdAt": SERVER_TIMESTAMP,
    }
    _, ref = _fs().collection("sessions").add(doc)
    ps = _fs().collection("users").document(payload.partner_uid).get()
    partner_name = ps.to_dict().get("displayName", "") if ps.exists else ""
    return _to_out(ref.id, doc, uid, partner_name)


async def get_my_sessions(uid: str) -> list[SessionOut]:

    snaps = (
        _fs()
        .collection("sessions")
        .where("participants", "array_contains", uid)
        .stream()
    )

    results = []

    for snap in snaps:

        data = snap.to_dict()

        partner_uid = next(
            (p for p in data.get("participants", []) if p != uid),
            ""
        )

        ps = _fs().collection("users").document(partner_uid).get()

        partner_name = ps.to_dict().get("displayName", "") if ps.exists else ""

        results.append(
            _to_out(
                snap.id,
                data,
                uid,
                partner_name
            )
        )

    results.sort(
        key=lambda x: x.date_time
    )

    return results


async def update_session(uid: str, session_id: str, payload: SessionUpdate) -> SessionOut | None:
    ref = _fs().collection("sessions").document(session_id)
    snap = ref.get()
    if not snap.exists:
        return None
    data = snap.to_dict()
    if uid not in data.get("participants", []):
        return None
    upd = {k: v for k, v in {"meetLink": payload.meet_link, "status": payload.status}.items() if v is not None}
    if upd:
        ref.update(upd)
    snap = ref.get()
    data = snap.to_dict()
    partner_uid = next((p for p in data.get("participants", []) if p != uid), "")
    ps = _fs().collection("users").document(partner_uid).get()
    partner_name = ps.to_dict().get("displayName", "") if ps.exists else ""
    return _to_out(session_id, data, uid, partner_name)
