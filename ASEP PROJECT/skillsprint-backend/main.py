from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import User
from routes.auth import router as auth_router

# Create tables in the database on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SkillSprint API",
    description="Competitive Coding and Hackathon Portal",
    version="1.0.0"
)

# CORS middleware - allows frontend to call backend
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://dreynox.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

