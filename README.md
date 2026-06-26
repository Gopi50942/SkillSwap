# SkillSwap — Complete Project

Peer-to-peer skill exchange platform.
Light/Dark iOS glassmorphism UI + Python FastAPI backend + Firebase.

## Structure
```
skillswap/
├── frontend/
│   └── index.html          # Full SPA — all 7 pages, light/dark drag switch
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── firebase.py
│   │   ├── middleware/auth.py
│   │   ├── models/schemas.py
│   │   ├── services/
│   │   │   ├── user_service.py
│   │   │   ├── match_service.py
│   │   │   ├── session_service.py
│   │   │   ├── review_service.py
│   │   │   ├── chat_service.py
│   │   │   └── leaderboard_service.py
│   │   └── routers/
│   │       ├── users.py
│   │       ├── matches.py
│   │       ├── sessions.py
│   │       ├── reviews.py
│   │       ├── chat.py
│   │       └── leaderboard.py
│   ├── requirements.txt
│   └── .env.example
├── firestore.rules
├── database.rules.json
├── firestore.indexes.json
└── firebase.json

```

## Quick start

### 1. Firebase setup
- Create project at https://console.firebase.google.com
- Enable Authentication (Email + Google)
- Enable Firestore Database
- Enable Realtime Database
- Download service account key → save as `backend/serviceAccountKey.json`
- Copy your web app config into `frontend/index.html` (firebaseConfig block)

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your values
uvicorn app.main:app --reload --port 8000
# Swagger → http://localhost:8000/docs
```

### 3. Frontend
```bash
# Just open frontend/index.html in a browser
# Or serve with Live Server (VS Code extension)
# Or: python -m http.server 5500 --directory frontend
```

### 4. Deploy rules
```bash
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules,firestore:indexes,database
```

### 5. Deploy frontend to Firebase Hosting
```bash
firebase deploy --only hosting
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/users/me | My profile |
| PUT | /api/v1/users/me | Update profile |
| GET | /api/v1/users/{uid} | Any user's profile |
| POST | /api/v1/users/me/skills/teach | Add teach skill |
| DELETE | /api/v1/users/me/skills/teach/{skill} | Remove teach skill |
| POST | /api/v1/users/me/skills/learn | Add learn skill |
| DELETE | /api/v1/users/me/skills/learn/{skill} | Remove learn skill |
| GET | /api/v1/matches/suggested | AI-ranked matches |
| GET | /api/v1/matches/ | My active matches |
| POST | /api/v1/matches/ | Connect with user |
| PATCH | /api/v1/matches/{id}/status | Update match status |
| POST | /api/v1/sessions/ | Schedule session |
| GET | /api/v1/sessions/ | My sessions |
| PATCH | /api/v1/sessions/{id} | Update session |
| POST | /api/v1/reviews/ | Submit review + auto-badge |
| GET | /api/v1/reviews/{uid} | User's reviews |
| POST | /api/v1/chat/send | Send chat message |
| GET | /api/v1/chat/{id}/messages | Chat history |
| GET | /api/v1/leaderboard/sessions | Top by sessions |
| GET | /api/v1/leaderboard/rating | Top by rating |
| GET | /api/v1/leaderboard/stats | Community stats |

## Connecting frontend to backend

In `frontend/index.html`, add this after firebase init:

```js
const API = 'http://localhost:8000/api/v1';

async function apiCall(path, method = 'GET', body = null) {
  const token = await firebase.auth().currentUser.getIdToken();
  const res = await fetch(API + path, {
    method,
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : null,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Usage examples:
const suggested = await apiCall('/matches/suggested');
const sessions  = await apiCall('/sessions/');
await apiCall('/sessions/', 'POST', {
  partner_uid: 'uid_here',
  topic: 'Python Pandas',
  date_time: '2026-06-28T18:00:00',
  duration: '60 minutes',
  meet_link: 'https://meet.google.com/abc'
});
await apiCall('/reviews/', 'POST', {
  to_uid: 'uid_here',
  session_id: 'sess_id',
  rating: 5,
  text: 'Amazing session!'
});
```

## Matching algorithm

```
score = (
  len(their_teach ∩ my_learn)  × 0.50
  len(my_teach ∩ their_learn)  × 0.40
  their_rating / 5             × 0.10
) / len(my_learn) × 100
```

## Badge auto-award (triggered on every review submit)

| Badge | Condition |
|-------|-----------|
| quick_starter | sessionsCount ≥ 1 |
| top_rated | rating ≥ 4.8 AND ratingCount ≥ 5 |
| verified_mentor | sessionsCount ≥ 10 |
| grand_mentor | sessionsCount ≥ 20 |
| legend | sessionsCount ≥ 50 |
