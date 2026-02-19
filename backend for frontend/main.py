from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models
import quiz_routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillSprint API")

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://dreynox.github.io",
    "https://skillsprint-muv2.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quiz_routes.router, prefix="/quiz", tags=["quiz"])


@app.get("/")
def root():
    return {"message": "SkillSprint backend running"}
