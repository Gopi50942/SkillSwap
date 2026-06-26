# SkillSwap — Python FastAPI + Firebase Backend

## Stack
| Layer              | Technology                        |
|--------------------|-----------------------------------|
| Backend framework  | FastAPI + Uvicorn                 |
| Auth verification  | Firebase Admin SDK (ID token)     |
| Profiles/Data      | Cloud Firestore                   |
| Real-time chat     | Firebase Realtime Database        |
| Hosting (frontend) | Firebase Hosting                  |
| Language           | Python 3.11+                      |

---

## Project structure
```
skillswap-backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router mounts
│   ├── config.py                # Settings (pydantic-settings + .env)
│   ├── firebase.py              # firebase-admin init (Firestore + RTDB)
│   ├── middleware/
│   │   └── auth.py              # Firebase ID token verification dep
│   ├── models/
│   │   └── schemas.py           # All Pydantic request/response models
│   ├── services/
│   │   ├── user_service.py      # Profile CRUD
│   │   ├── match_service.py     # Matching engine + match CRUD
│   │   ├── session_service.py   # Session CRUD
│   │   ├── review_service.py    # Reviews + badge award logic
│   │   ├── chat_service.py      # Realtime DB chat
│   │   └── leaderboard_service.py
│   └── routers/
│       ├── users.py
│       ├── matches.py
│       ├── sessions.py
│       ├── reviews.py
│       ├── chat.py
│       └── leaderboard.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Clone & install
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Firebase service account key
- Firebase Console → Project Settings → Service Accounts → Generate new private key
- Save as `serviceAccountKey.json` in project root

### 3. Configure .env
```bash
cp .env.example .env
# Fill in your Firebase project values
```

### 4. Run
```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI → http://localhost:8000/docs  
ReDoc     → http://localhost:8000/redoc

---

## API Reference

### Auth
Every protected endpoint requires:
```
Authorization: Bearer <Firebase ID Token>
```
Get the token from the Firebase JS SDK:
```js
const token = await firebase.auth().currentUser.getIdToken();
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/users/ | Create profile (after first login) |
| GET | /api/v1/users/me | Get my profile |
| PUT | /api/v1/users/me | Update profile |
| GET | /api/v1/users/{uid} | Get any user's profile |
| POST | /api/v1/users/me/skills/teach | Add teach skill |
| DELETE | /api/v1/users/me/skills/teach/{skill} | Remove teach skill |
| POST | /api/v1/users/me/skills/learn | Add learn skill |
| DELETE | /api/v1/users/me/skills/learn/{skill} | Remove learn skill |
| GET | /api/v1/matches/suggested | Get AI-ranked suggested matches |
| GET | /api/v1/matches/ | Get my active matches |
| POST | /api/v1/matches/ | Connect with another user |
| PATCH | /api/v1/matches/{id}/status | Update match status |
| POST | /api/v1/sessions/ | Schedule a session |
| GET | /api/v1/sessions/ | Get my sessions |
| PATCH | /api/v1/sessions/{id} | Update session (add link, cancel) |
| POST | /api/v1/reviews/ | Submit post-session review |
| GET | /api/v1/reviews/{uid} | Get reviews for a user |
| POST | /api/v1/chat/send | Send a chat message (RTDB) |
| GET | /api/v1/chat/{chat_id}/messages | Get chat history |
| GET | /api/v1/chat/id/{other_uid} | Get chat room ID |
| GET | /api/v1/leaderboard/sessions | Top users by sessions |
| GET | /api/v1/leaderboard/rating | Top users by rating |
| GET | /api/v1/leaderboard/stats | Community stats |
| GET | /health | Health check |

---

## Matching Algorithm

```
match_score(me, other) =
  ( skills_other_teaches ∩ skills_I_want    × 0.50
  + skills_I_teach       ∩ skills_other_wants × 0.40
  + other.rating / 5                          × 0.10 )
  ÷ len(my_skills_learn) × 100
```

- Score ≥ 85 → High match (green ring)
- Score < 85 → Good match (amber ring)

## Badge Engine

Badges auto-awarded in `review_service.py` after every review submission:

| Badge ID         | Condition                          |
|------------------|------------------------------------|
| quick_starter    | sessionsCount ≥ 1                  |
| top_rated        | rating ≥ 4.8 AND ratingCount ≥ 5  |
| verified_mentor  | sessionsCount ≥ 10                 |
| grand_mentor     | sessionsCount ≥ 20                 |
| legend           | sessionsCount ≥ 50                 |

## Frontend → Backend wiring

In your `public/index.html`, replace the Firebase-direct calls with:
```js
const API = 'http://localhost:8000/api/v1';  // or your deployed URL

async function apiCall(path, method='GET', body=null) {
  const token = await firebase.auth().currentUser.getIdToken();
  const res = await fetch(API + path, {
    method,
    headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : null,
  });
  return res.json();
}

// Examples:
const matches  = await apiCall('/matches/suggested');
const sessions = await apiCall('/sessions/');
await apiCall('/sessions/', 'POST', { partner_uid, topic, date_time, duration, meet_link });
await apiCall('/reviews/', 'POST', { to_uid, session_id, rating, text });
```
