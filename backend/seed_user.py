#!/usr/bin/env python3
"""
Seed script to add test users to the database
Run from parent directory: python -m backend.seed_user
Or from backend directory: python seed_user.py
"""

from .database import SessionLocal, engine, Base
from .models import User, RoleEnum
from .auth import hash_password

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Test user credentials provided by the user
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

try:
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            print(f"✓ User already exists: {user_data['email']}")
            continue
        
        # Create new user
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
        
        print(f"✓ User created successfully: {user_data['email']}")
    
    print("\n✓ Database seeding completed!")
    print(f"\nTest credentials:")
    print(f"  Email: {test_users[0]['email']}")
    print(f"  Password: {test_users[0]['password']}")
    
except Exception as e:
    db.rollback()
    print(f"✗ Error: {str(e)}")
finally:
    db.close()
