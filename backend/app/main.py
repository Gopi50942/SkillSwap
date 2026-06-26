import threading
import webbrowser
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.firebase import init_firebase
from app.routers import users, matches, sessions, reviews, chat, leaderboard

settings = get_settings()

app = FastAPI(
    title="SkillSwap API",
    description="Peer-to-peer skill exchange — FastAPI + Firebase",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve frontend ──────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h2>Frontend not found. Place index.html in the frontend/ folder.</h2>")

# ── Startup ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_firebase()
    # Auto-open browser after 1 second (gives server time to start)
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open("http://localhost:8000")
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n✅ SkillSwap is running!")
    print("🌐 Open: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs\n")

# ── API Routes ───────────────────────────────────────────────
app.include_router(users.router,       prefix="/api/v1")
app.include_router(matches.router,     prefix="/api/v1")
app.include_router(sessions.router,    prefix="/api/v1")
app.include_router(reviews.router,     prefix="/api/v1")
app.include_router(chat.router,        prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}