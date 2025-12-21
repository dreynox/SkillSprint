from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import User
from auth import router as auth_router

# Create tables in the database on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SkillSprint API",
    description="Competitive Coding and Hackathon Portal",
    version="1.0.0"
)

# CORS middleware - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# Health check endpoint
@app.get("/")
def read_root():
    return {
        "message": "SkillSprint API is running",
        "version": "1.0.0"
    }

# Run command: uvicorn main:app --reload

