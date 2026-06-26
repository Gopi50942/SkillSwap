from app.firebase import get_firestore
from app.models.schemas import LeaderboardEntry


def _fs():
    return get_firestore()


async def get_leaderboard_by_sessions(limit: int = 10) -> list[LeaderboardEntry]:
    snaps = (_fs().collection("users")
             .order_by("sessionsCount", direction="DESCENDING")
             .limit(limit).stream())
    return [LeaderboardEntry(
        uid=s.id,
        display_name=s.to_dict().get("displayName",""),
        college=s.to_dict().get("college",""),
        sessions_count=s.to_dict().get("sessionsCount",0),
        rating=s.to_dict().get("rating",0.0),
        badges=s.to_dict().get("badges",[]),
    ) for s in snaps]


async def get_leaderboard_by_rating(limit: int = 10) -> list[LeaderboardEntry]:
    snaps = (_fs().collection("users")
             .where("ratingCount",">=",3)
             .order_by("ratingCount",direction="DESCENDING")
             .order_by("rating",direction="DESCENDING")
             .limit(limit).stream())
    return [LeaderboardEntry(
        uid=s.id,
        display_name=s.to_dict().get("displayName",""),
        college=s.to_dict().get("college",""),
        sessions_count=s.to_dict().get("sessionsCount",0),
        rating=s.to_dict().get("rating",0.0),
        badges=s.to_dict().get("badges",[]),
    ) for s in snaps]


async def get_community_stats() -> dict:
    snaps = list(_fs().collection("users").stream())
    total_sessions = sum(s.to_dict().get("sessionsCount",0) for s in snaps)
    return {
        "total_users":    len(snaps),
        "total_sessions": total_sessions,
        "hours_exchanged": round(total_sessions * 0.85, 1),
    }
