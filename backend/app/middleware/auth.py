from fastapi import Request, HTTPException, status
from app.firebase import get_auth


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency — verifies Firebase ID token from
    Authorization: Bearer <token> header.
    Returns decoded token dict with uid, email, name, etc.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.split(" ", 1)[1]
    try:
        return get_auth().verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )
