# SkillSprint Setup & Debug Guide

## Fixed Issues ✓

### 1. **CORS Configuration** 
- ✓ Updated `backend/main.py` to include localhost ports (5500, 8000, 8080, 3000)
- ✓ Updated `backend for frontend/main.py` with same localhost origins
- ✓ Frontend now detects if running locally and uses `http://localhost:8000` API

### 2. **CSS Not Loading to index.html**
- ✓ Verified path is correct: `<link rel="stylesheet" href="frontend/css/login.css" />`
- ✓ **IMPORTANT**: Must serve via web server, NOT as file:// 
- ✓ Added error message container to display login errors

### 3. **Login Flow**
- ✓ Fixed redirect path from `dashboard.html` → `frontend/html/dashboard.html`
- ✓ API URL now dynamically selects local or production backend

---

## How to Set Up & Test Locally

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Seed Test User
```bash
cd backend
python seed_user.py
```

This will add your test credentials to the database:
- **Email**: rayhaan.shaikh25@vupune.ac.in
- **Password**: 31251209

### Step 3: Start the Backend Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend will be running at: `http://localhost:8000`

### Deploy the Backend on Render
- Use the `render.yaml` blueprint in the repository root.
- Deploy from the `render-main` branch.
- Render will provision the `skillsprint-backend` web service and `skillsprint-db` database.
- The backend reads `DATABASE_URL` from Render and falls back to SQLite locally.

### Step 4: Serve the Frontend
You MUST use a web server (not file://). Choose one:

#### Option A: Using Python
```bash
cd SkillSprint
python -m http.server 5500
```

#### Option B: Using VS Code Live Server Extension
- Install "Live Server" extension in VS Code
- Right-click on `index.html` → "Open with Live Server"
- It will open at `http://localhost:5500`

### Step 5: Test Login
1. Open `http://localhost:5500/index.html`
2. CSS should now load properly (green neon theme)
3. Use test credentials:
   - **Email**: rayhaan.shaikh25@vupune.ac.in
   - **Password**: 31251209
4. Check browser console (F12) for API debugging

---

## What Was Fixed

### Frontend Changes (`frontend/js/login.js`)
```javascript
// BEFORE: Hardcoded deployed URL
const API_BASE_URL = "https://skillsprint-muv2.onrender.com";

// AFTER: Detects local vs deployed
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isDev 
  ? `http://${window.location.hostname}:8000` 
  : "https://skillsprint-muv2.onrender.com";
```

### Backend Changes (`backend/main.py`)
```python
# Added multiple localhost origins for CORS
allow_origins=[
    "http://localhost:5500",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    # ... other origins
]
```

---

## Troubleshooting

### CSS Still Not Loading?
- Make sure you're serving via HTTP (not file://)
- Check browser DevTools → Network tab
- Verify path: should be `frontend/css/login.css`

### Login Still Getting CORS Error?
- Confirm backend is running on port 8000: `http://localhost:8000`
- Check browser console for exact error message
- Verify CORS middleware is loaded in both backends

### "Invalid email or password" Error?
- Run `python seed_user.py` in backend folder
- Check database exists: `backend/skillsprint.db`
- Check console for any SQL errors

### Can't Connect to Backend?
- Make sure `uvicorn main:app --reload --port 8000` is running
- Test with: `curl http://localhost:8000/`
- Should return: `{"message": "SkillSprint API is running", "version": "1.0.0"}`

---

## Database File
- **Location**: `backend/skillsprint.db`
- **Type**: SQLite
- To reset database: Delete the file and re-run backend (creates fresh DB)

---
