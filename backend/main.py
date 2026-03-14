from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, ensure_sqlite_compatibility
from routes import auth_routes, contest_routes, quiz_routes

# ---------- APP & DATABASE SETUP ----------

ensure_sqlite_compatibility()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillSprint API",
    description="SkillSprint - Competitive Coding and Hackathon Portal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://dreynox.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "SkillSprint API is running", "docs": "/docs"}


app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(quiz_routes.router, prefix="/quiz", tags=["quiz"])
app.include_router(contest_routes.router, prefix="/contests", tags=["contests"])
