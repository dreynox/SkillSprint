#!/usr/bin/env python3
"""
Comprehensive seed script to initialize database with users and sample quizzes
Run from parent directory: python -m backend.seed_user
Or from backend directory: python seed_user.py
"""

from .database import SessionLocal, engine, Base
from .models import User, Quiz, QuizQuestion, RoleEnum
from .auth import hash_password

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Test users
test_users = [
    {
        "name": "Rayhaan Shaikh",
        "email": "rayhaan.shaikh25@vupune.ac.in",
        "password": "31251209",
        "year": "3",
        "branch": "CSE",
        "role": RoleEnum.STUDENT
    },
    {
        "name": "Test Admin",
        "email": "admin@skillsprint.com",
        "password": "admin123",
        "year": "4",
        "branch": "CSE",
        "role": RoleEnum.ADMIN
    }
]

# Sample quizzes with questions
sample_quizzes = [
    {
        "title": "FastAPI Basics",
        "description": "Learn the fundamentals of FastAPI",
        "is_active": True,
        "questions": [
            {
                "text": "What does FastAPI mainly help you build?",
                "option_a": "Machine learning models",
                "option_b": "REST APIs",
                "option_c": "Operating systems",
                "option_d": "Mobile games",
                "correct_option": "B",
            },
            {
                "text": "Which HTTP method is usually used to submit a form?",
                "option_a": "GET",
                "option_b": "POST",
                "option_c": "PUT",
                "option_d": "DELETE",
                "correct_option": "B",
            },
            {
                "text": "What does CORS stand for?",
                "option_a": "Cross-Origin Resource Sharing",
                "option_b": "Cross-Server Object Replication System",
                "option_c": "Cached Online Resource Server",
                "option_d": "Code Organization and Routing System",
                "correct_option": "A",
            }
        ]
    },
    {
        "title": "Python Fundamentals",
        "description": "Test your Python knowledge",
        "is_active": True,
        "questions": [
            {
                "text": "What is the correct way to create a list in Python?",
                "option_a": "[1, 2, 3]",
                "option_b": "(1, 2, 3)",
                "option_c": "{1, 2, 3}",
                "option_d": "<1, 2, 3>",
                "correct_option": "A",
            },
            {
                "text": "Which keyword is used to create a function in Python?",
                "option_a": "function",
                "option_b": "def",
                "option_c": "define",
                "option_d": "func",
                "correct_option": "B",
            }
        ]
    }
]

try:
    # Seed users
    print("📝 Seeding users...")
    for user_data in test_users:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            print(f"✓ User already exists: {user_data['email']}")
            continue
        
        new_user = User(
            name=user_data["name"],
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            year=int(user_data["year"]) if user_data.get("year") else None,
            branch=user_data.get("branch"),
            role=user_data.get("role", RoleEnum.STUDENT)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✓ User created: {user_data['email']}")
    
    # Seed quizzes with questions
    print("\n📝 Seeding quizzes...")
    for quiz_data in sample_quizzes:
        existing_quiz = db.query(Quiz).filter(Quiz.title == quiz_data["title"]).first()
        
        if existing_quiz:
            print(f"✓ Quiz already exists: {quiz_data['title']}")
            continue
        
        quiz = Quiz(
            title=quiz_data["title"],
            description=quiz_data.get("description"),
            is_active=quiz_data.get("is_active", False)
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Add questions to the quiz
        for question_data in quiz_data.get("questions", []):
            question = QuizQuestion(
                quiz_id=quiz.id,
                text=question_data["text"],
                option_a=question_data["option_a"],
                option_b=question_data["option_b"],
                option_c=question_data["option_c"],
                option_d=question_data["option_d"],
                correct_option=question_data["correct_option"]
            )
            db.add(question)
        
        db.commit()
        print(f"✓ Quiz created with {len(quiz_data.get('questions', []))} questions: {quiz_data['title']}")
    
    print("\n✅ Database seeding completed!")
    print(f"\nTest credentials:")
    print(f"  Email: {test_users[0]['email']}")
    print(f"  Password: {test_users[0]['password']}")
    print(f"\nSample quizzes created:")
    for quiz_data in sample_quizzes:
        print(f"  - {quiz_data['title']} ({len(quiz_data.get('questions', []))} questions)")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {str(e)}")
finally:
    db.close()
