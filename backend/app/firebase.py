import firebase_admin
from firebase_admin import credentials, firestore, auth, db as rtdb
from app.config import get_settings

_initialized = False


def init_firebase():
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        "databaseURL": settings.firebase_database_url
    })
    _initialized = True


def get_firestore():
    init_firebase()
    return firestore.client()


def get_rtdb():
    init_firebase()
    return rtdb


def get_auth():
    init_firebase()
    return auth
