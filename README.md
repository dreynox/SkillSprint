SkillSprint – Competitive Coding & Hackathon Portal
SkillSprint is a full‑stack web platform for competitive coding, MCQ quizzes, hackathons, projects, and tech events. It is built as an ASEP/capstone project to centralize opportunities for students and provide real‑time contests, scores, and analytics.

Features
Central hub for coding contests, quizzes, and college events in one place instead of scattered WhatsApp messages and notices.

MCQ quiz engine:

Question bank stored in the backend database

Host/activate tests for specific batches

Auto‑evaluation of submissions

Admin view of students’ scores and timestamps
​

REST API backend using FastAPI + SQLAlchemy (in backend/).

Static frontend (HTML, CSS, JS) served via GitHub Pages from this repo (root index.html and frontend/).

Tech Stack
Frontend:

HTML, CSS, JavaScript in index.html and frontend/ for the SkillSprint UI and quiz page.

Backend:

FastAPI (Python) for APIs (auth, quizzes, events – work in progress).
​

SQLAlchemy ORM with SQLite for local development (can switch to PostgreSQL/MySQL later).

Deployment:

GitHub Pages for hosting the static frontend (main branch).
​

(Planned/used) Render or similar service for hosting the FastAPI backend.
​

Project Structure
text
SkillSprint/
├── backend/              # FastAPI backend (APIs, DB models, quiz engine)
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── quiz_routes.py
│   ├── seed_data.py
│   └── requirements.txt
├── frontend/             # Additional frontend assets/pages
│   └── ...               # HTML, CSS, JS files for dashboard & UI
├── index.html            # Landing / main page for GitHub Pages
├── .python-version       # Python runtime hint for the project
└── runtime.txt           # Runtime hint for hosting platforms
(The exact file list may evolve as new features are added.)

Backend API Overview (Quiz Module)
Quiz endpoints are mounted under /quiz on the FastAPI backend:

GET /quiz/tests/{test_id}/questions
Returns all questions for a given test (id, text, options A–D), without exposing correct answers.

POST /quiz/tests/{test_id}/submit
Accepts user answers, calculates score, saves a Submission record, and responds with { score, total }.

GET /quiz/admin/tests/{test_id}/submissions
Returns all submissions for that test (user_id, score, submitted_at) for admin/teacher marks view.

Getting Started – Backend (Local)
1. Go to backend folder
bash
cd backend
2. Create and activate virtual environment (Python 3.11)
bash
py -3.11 -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/macOS
3. Install dependencies
bash
python -m pip install --upgrade pip
pip install -r requirements.txt
4. Run FastAPI server
bash
uvicorn main:app --reload
API root: http://127.0.0.1:8000/

Swagger UI: http://127.0.0.1:8000/docs

5. Seed sample quiz data (optional)
bash
python seed_data.py
This creates a sample test and a few MCQs in skillsprint.db and prints the test ID used.
​

Getting Started – Frontend (Local)
Simple static preview
Open index.html in a browser or use a local static server (recommended):

bash
# from repo root
python -m http.server 5500
Then open:

http://127.0.0.1:5500/index.html – main SkillSprint UI

(If you have a dedicated quiz page) http://127.0.0.1:5500/frontend/quiz.html etc.

Configure CORS in the backend to allow http://127.0.0.1:5500 and your GitHub Pages origin (https://dreynox.github.io).

Roadmap
Planned and ongoing work for SkillSprint:

Full dashboard for contests, hackathons, and project listings.

User authentication with roles (student/admin), profiles, and participation history.
​

Admin UI to create/edit tests and questions from the browser (no manual seed scripts).

Timed quizzes, per‑question analytics, and richer result pages.
​

Coding challenge support (problem statements, submissions, leaderboards).

Stable deployment: FastAPI backend on Render + static frontend on GitHub Pages.
​

Contributing
This is currently a personal/academic project, but suggestions and issue reports are welcome via GitHub Issues.
