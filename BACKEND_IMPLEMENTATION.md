# SkillSprint Backend - Unified API Implementation

## ✅ What Was Done

### 1. **Fixed and Enhanced Models** (`backend/models.py`)
- ✅ Added missing imports: `Boolean`, `ForeignKey`, `relationship`
- ✅ Fixed Contest models with proper relationships and cascading deletes
- ✅ Merged Quiz models from experimental backend (Test → Quiz, Question → QuizQuestion, QuizSubmission)
- ✅ Added proper foreign key relationships between all models

**Models now include:**
- `User` - User authentication and profile
- `Contest` - Coding contests
- `ContestProblem` - Contest problems
- `ContestSubmission` - Code submissions for contests
- `Quiz` - MCQ quizzes/tests
- `QuizQuestion` - Quiz questions with 4 options
- `QuizSubmission` - Quiz submission results

### 2. **Created Complete Schemas** (`backend/schemas.py`)
Added Pydantic models for all operations:
- **Auth**: `UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse`
- **Contests**: `ContestCreate`, `ContestResponse`, `ProblemCreate`, `ProblemResponse`, `SubmissionCreate`, `SubmissionResponse`, `LeaderboardEntry`
- **Quizzes**: `QuizCreate`, `QuizResponse`, `QuestionCreate`, `QuestionResponse`, `QuestionAdminResponse`, `QuizAnswer`, `QuizSubmissionCreate`, `QuizSubmissionResponse`

### 3. **Enhanced Authentication** (`backend/auth.py`)
- ✅ Added `get_current_user()` dependency - extracts user from JWT token in Authorization header
- ✅ Added `require_admin()` dependency - ensures only admins can access certain endpoints
- ✅ Uses HTTPBearer security for protected routes

### 4. **Created Contest Routes** (`backend/routes/contest_routes.py`)

#### Public Endpoints:
- `GET /contests` - List all contests
- `GET /contests/{id}` - Get contest details
- `GET /contests/{id}/problems` - List problems in a contest
- `GET /contests/{id}/leaderboard` - View submissions/leaderboard

#### Protected Endpoints (require login):
- `POST /contests/{id}/submit` - Submit a solution
- `GET /contests/{id}/my-submissions` - View your submissions

#### Admin Endpoints:
- `POST /contests` - Create a new contest
- `POST /contests/{id}/problems` - Add problem to contest

### 5. **Created Quiz Routes** (`backend/routes/quiz_routes.py`)

#### Public Endpoints:
- `GET /quiz/` - List all quizzes
- `GET /quiz/{id}` - Get quiz details
- `GET /quiz/{id}/questions` - Get questions (without answers)

#### Protected Endpoints (require login):
- `POST /quiz/{id}/submit` - Submit quiz answers
- `GET /quiz/{id}/my-submissions` - View your quiz submissions

#### Admin Endpoints:
- `POST /quiz/` - Create a new quiz
- `POST /quiz/{id}/questions` - Add question to quiz
- `GET /quiz/admin/{id}/questions` - Get questions with correct answers
- `GET /quiz/admin/{id}/submissions` - View all submissions

### 6. **Updated Main App** (`backend/main.py`)
- ✅ Fixed broken imports
- ✅ Registered both routers:
  - `/contests` - Contest endpoints
  - `/quiz` - Quiz endpoints
- ✅ Kept existing auth endpoints (`/auth/register`, `/auth/login`)
- ✅ Maintained CORS configuration for GitHub Pages and local dev

---

## 🏗️ Final Backend Structure

```
backend/
├── __init__.py
├── main.py                 # FastAPI app with auth + routers ✅
├── config.py               # SECRET_KEY config ✅
├── database.py             # SQLite setup ✅
├── auth.py                 # Auth functions + dependencies ✅
├── models.py               # All DB models (User, Contest, Quiz, etc.) ✅
├── schemas.py              # All Pydantic schemas ✅
├── seed_user.py            # (existing)
├── requirements.txt        # (existing)
└── routes/
    ├── __init__.py         # Routes package ✅
    ├── contest_routes.py   # Contest endpoints ✅
    └── quiz_routes.py      # Quiz endpoints ✅
```

---

## 🚀 How to Run

1. **Install dependencies** (if not already):
```bash
cd backend
pip install -r requirements.txt
```

2. **Run the server**:
```bash
uvicorn main:app --reload
```

Or from the project root:
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **Access the API**:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

---

## 📝 API Usage Examples

### 1. Register a User
```bash
POST /auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "year": 2,
  "branch": "CSE"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "year": 2,
    "branch": "CSE",
    "role": "student"
  }
}
```

### 2. Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}
```

### 3. Create a Contest (Admin Only)
```bash
POST /contests
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "name": "Weekly Coding Challenge #1",
  "description": "Solve algorithmic problems",
  "is_active": true,
  "start_time": "2026-03-15T10:00:00",
  "end_time": "2026-03-15T12:00:00"
}
```

### 4. Add a Problem to Contest (Admin Only)
```bash
POST /contests/1/problems
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "title": "Two Sum",
  "statement": "Given an array of integers, return indices of two numbers that add up to a target.",
  "difficulty": "Easy",
  "max_score": 100
}
```

### 5. List All Contests
```bash
GET /contests
```

### 6. Get Contest Problems
```bash
GET /contests/1/problems
```

### 7. Submit a Solution (Authenticated)
```bash
POST /contests/1/submit
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "problem_id": 1,
  "language": "Python",
  "code": "def two_sum(nums, target):\n    # solution here\n    pass"
}
```

### 8. View Leaderboard
```bash
GET /contests/1/leaderboard
```

### 9. Create a Quiz (Admin Only)
```bash
POST /quiz/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "title": "Python Basics Quiz",
  "description": "Test your Python knowledge",
  "is_active": true
}
```

### 10. Add Question to Quiz (Admin Only)
```bash
POST /quiz/1/questions
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "text": "What is the output of print(type([]))?",
  "option_a": "<class 'list'>",
  "option_b": "<class 'dict'>",
  "option_c": "<class 'tuple'>",
  "option_d": "<class 'set'>",
  "correct_option": "A"
}
```

### 11. Get Quiz Questions
```bash
GET /quiz/1/questions
```

### 12. Submit Quiz Answers (Authenticated)
```bash
POST /quiz/1/submit
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "answers": [
    {"question_id": 1, "selected": "A"},
    {"question_id": 2, "selected": "C"}
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "quiz_id": 1,
  "score": 2,
  "total_questions": 2,
  "submitted_at": "2026-03-10T12:34:56"
}
```

---

## 🔐 Authentication Flow

1. **Register or Login** → Get `access_token`
2. **Use token in subsequent requests**:
   ```
   Authorization: Bearer <your_access_token>
   ```
3. **Access protected endpoints** (submit, view submissions, etc.)
4. **Admin endpoints** require `role: "admin"` in user profile

---

## 🎯 Key Features

### Contest Module
✅ Create contests with start/end times
✅ Add multiple problems per contest
✅ Submit code solutions (text stored, judging manual/PENDING)
✅ View leaderboard ordered by score and submission time
✅ Users can view their own submissions

### Quiz Module
✅ Create MCQ quizzes with multiple questions
✅ Questions have 4 options (A/B/C/D)
✅ Automatic scoring on submission
✅ Public endpoints don't reveal correct answers
✅ Admin can view all submissions and questions with answers

### Security
✅ JWT-based authentication
✅ Password hashing with bcrypt
✅ Role-based access control (student/admin/faculty)
✅ Token validation on protected routes
✅ CORS configured for GitHub Pages + local dev

---

## 🧪 Testing with FastAPI Docs

1. Start the server
2. Go to http://localhost:8000/docs
3. Click "Authorize" button
4. Enter: `Bearer <your_token>` (get token from login/register)
5. Try out the endpoints interactively!

---

## 📊 Database

- **Engine**: SQLite (local development)
- **File**: `backend/skillsprint.db` (auto-created)
- **Tables**: users, contests, contest_problems, contest_submissions, quizzes, quiz_questions, quiz_submissions
- **Relationships**: Properly defined with cascading deletes

To reset the database, simply delete `skillsprint.db` and restart the server.

---

## 🔄 Next Steps (Optional Enhancements)

1. **Add automated judging** for contest submissions (integrate with Judge0 API or similar)
2. **Add time limits** and validation for contest/quiz active periods
3. **Add pagination** for large result sets
4. **Add filtering/search** for contests and quizzes
5. **Add test cases** to problems for validation
6. **Add user profile endpoints** (update profile, change password)
7. **Add email verification** for registration
8. **Add submission statistics** (attempts, success rate, etc.)
9. **Add tags/categories** for contests and quizzes
10. **Add websockets** for real-time leaderboard updates

---

## 🐛 Troubleshooting

### Import errors in IDE
The import errors you see are just VS Code not finding the packages. They'll work fine when you run the server with the dependencies installed.

### Database errors
Delete `backend/skillsprint.db` to reset. Models will auto-create tables on startup.

### CORS errors
Make sure your frontend origin is in the `allow_origins` list in `main.py`.

### Authentication errors
- Check token format: `Authorization: Bearer <token>`
- Ensure token hasn't expired (2 hour default)
- Verify user exists in database

---

## ✨ Summary

You now have a **fully unified backend** with:
- ✅ User authentication (register/login)
- ✅ Contest management (create, add problems, submit code, view leaderboard)
- ✅ Quiz management (create, add questions, submit answers, auto-scoring)
- ✅ Role-based access control (admin vs student)
- ✅ Clean REST API with proper schemas
- ✅ Single database for everything
- ✅ Ready to integrate with your frontend

All code is in the `backend/` directory, and the experimental `backend for frontend/` can now be safely ignored or deleted.
