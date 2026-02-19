from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

def seed():
    db: Session = SessionLocal()

    # 1) Create a test
    test = models.Test(
        title="Sample MCQ Test",
        description="Demo quiz for SkillSprint",
        is_active=True,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    test_id = test.id  # store id before closing session

    # 2) Add a few questions
    q1 = models.Question(
        test_id=test_id,
        text="What does FastAPI mainly help you build?",
        option_a="Machine learning models",
        option_b="REST APIs",
        option_c="Operating systems",
        option_d="Mobile games",
        correct_option="B",
    )
    q2 = models.Question(
        test_id=test_id,
        text="Which HTTP method is usually used to submit a form?",
        option_a="GET",
        option_b="POST",
        option_c="PUT",
        option_d="DELETE",
        correct_option="B",
    )

    db.add_all([q1, q2])
    db.commit()
    db.close()

    print("Seeded test with id:", test_id)
