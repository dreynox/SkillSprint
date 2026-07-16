<div align="center">

<h1>SkillSprint - Empowering Future Coders</h1>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](http://makeapullrequest.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**SkillSprint is a full-stack ASEP/capstone project that centralizes coding contests, MCQ quizzes, hackathons, and tech opportunities for students.**

[🌐 Live Demo](https://dreynox.github.io/SkillSprint)

</div>

---

## Table of Contents

- [🚀 About SkillSprint](#-about-skillsprint)
- [✨ Key Features](#-key-features)
- [🛠️ Technology Stack](#%EF%B8%8F-technology-stack)
- [⚡ Quick Start Guide](#-quick-start-guide)
- [🤝 Contributing Guidelines](#-contributing-guidelines)
- [📜 Rules & Conditions](#-rules--conditions)
- [📖 API Documentation](#-api-documentation)
- [📄 License](#-license)
- [💬 Community & Support](#-community--support)

---

## 🚀 About SkillSprint

SkillSprint is a comprehensive full-stack web application designed to act as a centralized platform for students and educators. It enables students to register, take tests, and participate in competitive programming challenges, while allowing educators to seamlessly host MCQ quizzes and coding contests.

Whether you're preparing for a hackathon, honing your technical skills, or managing a coding contest, SkillSprint has you covered.

## ✨ Key Features

| Feature                               | Description                                                                   |
| ------------------------------------- | ----------------------------------------------------------------------------- |
| 🎓 **Student Registration & Login**   | Secure authentication and session management. |
| 🧑‍🏫 **Admin/Teacher Dashboard**    | Host and manage quiz tests and coding contests easily. |
| 📝 **MCQ Quizzes & Scoring**          | Real-time attempt tracking and score storage. |
| 💻 **Coding Contest Engine**          | Create contest submissions and execute code dynamically. |
| 🚀 **Multi-Language Compiler**        | Execute code in C, C++, Python, JavaScript, Java, Go, Rust, and more. |
| 📚 **API Swagger Documentation**      | Explore and interact with APIs seamlessly using FastAPI's Swagger UI. |

## 🛠️ Technology Stack

### Backend Architecture

```text
FastAPI (High-performance web framework)
├── SQLAlchemy (ORM for database operations)
├── SQLite (Local database)
├── PostgreSQL (Production database on Render)
└── Docker (Containerization for compiler toolchains)
```

### Frontend Architecture

```text
Vanilla JavaScript + HTML/CSS
├── API Client Logic
└── Responsive Layout Design
```

## ⚡ Quick Start Guide

Follow these instructions to host the project locally on your machine.

### Prerequisites

- **Python** (v3.8 or higher)
- **Node.js** (optional, for some frontend build/serve tools)
- **Docker** (optional, recommended for compiler engine testing)
- **PostgreSQL** (optional for local, defaults to SQLite)

### 📥 Installation Steps

#### 1️⃣ Fork & Clone the Repository

Fork the repository to your GitHub account, then clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/SkillSprint.git
cd SkillSprint
```

#### 2️⃣ Backend Setup

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 3️⃣ Seed Database & Run Server

```bash
# Seed the local SQLite database
python seed_data.py

# Start the FastAPI server
uvicorn main:app --reload
# Server runs on http://127.0.0.1:8000
```

*To access API Documentation, visit: `http://127.0.0.1:8000/docs`*

#### 4️⃣ Frontend Setup

Open a new terminal window in the project root:

```bash
python -m http.server 5500
```
*Frontend runs on `http://127.0.0.1:5500/index.html`*

#### 🐳 Docker Setup (Compiler-Ready)

If you wish to test the multi-language compiler functionalities:

```bash
docker build -t skillsprint-backend .
docker run -p 8000:8000 --env-file backend/.env skillsprint-backend
```

---

## 🤝 Contributing Guidelines

We are participating in the **Elite Coders Summer of Code 2026** and welcome open-source contributors! Here is exactly how you can contribute:

### 🛠️ Setting Up Your Contribution Workflow

1. **Fork the Repository**: Click the "Fork" button at the top right of this page.
2. **Clone your Fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/SkillSprint.git
   cd SkillSprint
   ```
3. **Set Upstream Remote**: Sync your fork with the original repository to keep it updated.
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/SkillSprint.git
   git fetch upstream
   ```

### 🎯 How to Raise and Claim Issues

1. Go to the [Issues](#) tab in the original repository.
2. If you find a bug or have a feature idea, **create a new issue**.
3. **Wait to be assigned**: Please comment on the issue you wish to work on and wait for a project admin to assign it to you before starting your work.
4. Once assigned, create a feature branch:
   ```bash
   git checkout -b feature/issue-number-description
   ```

### 📝 Issue Description Guidelines

When creating an issue, please ensure it follows this structure:
- **Title**: Short and descriptive (e.g., `Bug: Login button unresponsive on mobile`).
- **Description**: Detailed explanation of the bug or feature.
- **Steps to Reproduce** (if bug): Clear steps to trigger the issue.
- **Expected vs Actual Behavior**.
- **Screenshots** (if applicable).

### 💬 Commit Message Guidelines

We follow Conventional Commits. Your commit messages must be clear and descriptive:
- `feat: add new compiler language support`
- `fix: resolve quiz scoring calculation error`
- `docs: update setup instructions in README`
- `ui: improve dashboard layout spacing`
- `chore: update dependencies`

### 📤 Pull Request (PR) Description Guidelines

When submitting a PR, your description must include:
- **Related Issue**: e.g., `Fixes #42`
- **What was changed**: A brief summary of your code changes.
- **How to test**: Steps for the reviewer to verify your changes.
- **Screenshots/Recordings**: Necessary for any UI-related changes.

## 📜 Rules & Conditions

To ensure a smooth collaboration, please abide by the following rules:
- **No Plagiarism**: All code submitted must be your own or properly attributed open-source code.
- **One Issue at a Time**: Do not claim multiple issues at once. Finish your assigned issue before requesting another.
- **Wait for Assignment**: PRs submitted without an assigned issue will be marked as spam or closed.
- **Code Quality**: Ensure your code is well-commented, clean, and follows existing repository structure and formatting.
- **Be Respectful**: Treat all community members, maintainers, and reviewers with kindness and respect.

## 📖 API Documentation

Our backend exposes comprehensive RESTful APIs. Here is a brief overview:

- **Auth**: `POST /auth/register`, `POST /auth/login`
- **Quizzes**: `GET /quiz/tests`, `POST /quiz/tests/{test_id}/submit`
- **Contests**: `GET /contests`, `POST /contests/{contest_id}/problems/{problem_id}/submit`
- **Compiler Engine**: `POST /compiler/run`, `POST /compiler/debug`

For full details, spin up the backend and visit `/docs`.

## 📄 License

This project is licensed under the **MIT License**.
- ✅ Use for personal or commercial purposes
- ✅ Modify the source code
- ✅ Distribute copies

## 💬 Community & Support

- 🐛 **GitHub Issues**: Report bugs or request features
- 🚀 **Discussions**: Engage with other contributors and ask questions

---

<div align="center">

### ⭐ If you liked this project or found it helpful, please give it a star! 🌟

### Made with ❤️ for the open-source community
</div>
