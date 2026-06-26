import time
from app.firebase import get_rtdb
from app.models.schemas import ChatMessage, MessageOut


def get_chat_id_for(uid1: str, uid2: str) -> str:
    return "__".join(sorted([uid1, uid2]))


async def send_message(uid: str, payload: ChatMessage) -> MessageOut:
    rdb = get_rtdb()
    msg = {
        "senderUid": uid,
        "text": payload.text.strip(),
        "timestamp": int(time.time() * 1000),
    }
    msg_ref = rdb.reference(f"chats/{payload.chat_id}/messages").push(msg)
    rdb.reference(f"chats/{payload.chat_id}/meta").update({
        "lastMessage":   msg["text"][:60],
        "lastSender":    uid,
        "lastTimestamp": msg["timestamp"],
    })
    return MessageOut(
        msg_id=msg_ref.key,
        sender_uid=uid,
        text=payload.text,
        timestamp=msg["timestamp"],
    )


async def get_messages(uid: str, chat_id: str, limit: int = 50) -> list[MessageOut]:
    rdb  = get_rtdb()
    snap = (rdb.reference(f"chats/{chat_id}/messages")
            .order_by_child("timestamp")
            .limit_to_last(limit)
            .get())
    if not snap:
        return []
    results = [
        MessageOut(
            msg_id=k,
            sender_uid=v.get("senderUid", ""),
            text=v.get("text", ""),
            timestamp=v.get("timestamp", 0),
        )
        for k, v in snap.items()
    ]
    results.sort(key=lambda m: m.timestamp)
    return results
async def create_chat(uid1: str, uid2: str, name1: str, name2: str):

    rdb = get_rtdb()

    chat_id = get_chat_id_for(uid1, uid2)

    ref = rdb.reference(f"chats/{chat_id}")

    if ref.get():
        return chat_id

    ref.set({

        "members": {
            uid1: True,
            uid2: True
        },

        "names": {
            uid1: name1,
            uid2: name2
        },

        "meta": {

            "lastMessage": "",

            "lastSender": "",

            "lastTimestamp": int(time.time()*1000)

        },

        "typing": {

            uid1: False,

            uid2: False

        },

        "unread": {

            uid1: 0,

            uid2: 0

        }

    })

    return chat_id
async def get_user_chats(uid: str):

    rdb = get_rtdb()

    chats = rdb.reference("chats").get()

    if not chats:

        return []

    result = []

    for chat_id, chat in chats.items():

        members = chat.get("members", {})

        if uid not in members:

            continue

        names = chat.get("names", {})

        other_uid = next(k for k in members if k != uid)

        meta = chat.get("meta", {})

        unread = chat.get("unread", {})

        result.append({

            "chat_id": chat_id,

            "partner_uid": other_uid,

            "partner_name": names.get(other_uid, "User"),

            "last_message": meta.get("lastMessage", ""),

            "last_time": meta.get("lastTimestamp", 0),

            "unread": unread.get(uid, 0)

        })

    result.sort(

        key=lambda x: x["last_time"],

        reverse=True

    )

    return result

async def mark_read(chat_id: str, uid: str):

    rdb = get_rtdb()

    rdb.reference(

        f"chats/{chat_id}/unread/{uid}"

    ).set(0)

    return True