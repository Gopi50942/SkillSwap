import json
import os

import firebase_admin
from firebase_admin import credentials, firestore, auth, db as rtdb

from app.config import get_settings

_initialized = False

def init_firebase():
    global _initialized

    if _initialized:
        return

    settings = get_settings()

    firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")

    print("ENV FOUND:", firebase_creds is not None)

    if firebase_creds:
        data = json.loads(firebase_creds)
        print("Project ID:", data.get("project_id"))
        print("Client Email:", data.get("client_email"))
        cred = credentials.Certificate(data)
    else:
        print("Using local serviceAccountKey.json")
        cred = credentials.Certificate(settings.firebase_credentials_path)

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": settings.firebase_database_url
        }
    )

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