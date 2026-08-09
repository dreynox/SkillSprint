import os
import sys
import traceback

# Ensure `backend/` is on sys.path whether uvicorn is launched from the repo
# root (python -m uvicorn backend.main:app) or from inside backend/ (uvicorn main:app).
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine, ensure_sqlite_compatibility
from routes import (
    auth_routes,
    chatbot_routes,
    compiler_routes,
    contest_routes,
    hackathon_routes,
    health_routes,
    message_routes,
    quiz_routes,
    user_routes,
)

# ---------- APP & DATABASE SETUP ----------

def initialize_database():
    try:
        ensure_sqlite_compatibility()
        Base.metadata.create_all(bind=engine)
        print("[startup] Database initialization completed")
    except Exception as exc:
        print(f"[startup] Database initialization failed: {exc}")
        traceback.print_exc()


initialize_database()

app = FastAPI(
    title="SkillSprint API",
    description="SkillSprint - Competitive Coding and Hackathon Portal",
    version="1.0.0",
)

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://dreynox.github.io",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.[0-9]{1,3}\.[0-9]{1,3}|.*\.onrender\.com)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "SkillSprint API is running", "docs": "/docs"}


app.include_router(health_routes.router, prefix="/health", tags=["health"])
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(quiz_routes.router, prefix="/quiz", tags=["quiz"])
app.include_router(contest_routes.router, prefix="/contests", tags=["contests"])
app.include_router(hackathon_routes.router, prefix="/hackathons", tags=["hackathons"])
app.include_router(user_routes.router, prefix="/users", tags=["users"])
app.include_router(message_routes.router, tags=["messages"])
app.include_router(compiler_routes.router, prefix="/compiler", tags=["compiler"])
app.include_router(chatbot_routes.router, prefix="/chatbot", tags=["chatbot"])
