# SkillSprint - Competitive Coding and Hackathon Portal

SkillSprint is a full-stack ASEP/capstone project that centralizes coding contests, MCQ quizzes, hackathons, and tech opportunities for students.

## What it does
- Lets students register and log in.
- Lets admins/teachers host quiz tests and coding contests.
- Lets students attempt MCQ tests and stores scores.
- Lets users create contest submissions (currently stored with `PENDING` verdict).
- Exposes all APIs through FastAPI Swagger docs.

## Backend stack
- FastAPI
- SQLAlchemy
- SQLite locally (`backend/skillsprint.db`)
- PostgreSQL on Render via `DATABASE_URL` using psycopg3

## Backend structure
- `backend/database.py`: DB engine, `SessionLocal`, `Base`, `get_db`
- `backend/models.py`: `User`, `Test`, `Question`, `QuizSubmission`, `Contest`, `ContestProblem`, `ContestSubmission`
- `backend/schemas.py`: Pydantic request/response models
- `backend/routes/auth_routes.py`: `/auth/register`, `/auth/login`
- `backend/routes/quiz_routes.py`: quiz endpoints
- `backend/routes/contest_routes.py`: contest endpoints
- `backend/main.py`: app init, CORS, router registration
- `backend/seed_data.py`: sample data seeding

## Run backend
```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed_data.py
uvicorn main:app --reload
```

## Migrate local data to Render Postgres
1. Set `DATABASE_URL` to your Render PostgreSQL connection string.
2. From the `backend` folder, run:
```bash
python migrate_sqlite_to_postgres.py
```
3. If you want to overwrite rows already in Postgres, run:
```bash
python migrate_sqlite_to_postgres.py --clear-target
```

Open:
- API root: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Run frontend (static)
From project root:
```bash
python -m http.server 5500
```

Open:
- Landing page: `http://127.0.0.1:5500/index.html`
- Quiz page: `http://127.0.0.1:5500/frontend/html/quiz.html`

## API overview

### Auth
- `POST /auth/register`
- `POST /auth/login`

### Quiz
- `GET /quiz/tests`
- `GET /quiz/tests/{test_id}/questions`
- `POST /quiz/tests/{test_id}/submit`
- `GET /quiz/admin/tests/{test_id}/submissions`

### Contests
- `POST /contests`
- `GET /contests`
- `GET /contests/{contest_id}`
- `POST /contests/{contest_id}/problems`
- `POST /contests/{contest_id}/problems/{problem_id}/submit`
- `GET /contests/{contest_id}/submissions`

## CORS origins configured
- `http://localhost:5500`
- `http://127.0.0.1:5500`
- `https://dreynox.github.io`
