from pydantic import BaseModel
from typing import List


class QuestionOut(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class Answer(BaseModel):
    question_id: int
    selected: str  # "A" / "B" / "C" / "D"


class SubmissionRequest(BaseModel):
    user_id: int          # later replace with auth
    answers: List[Answer]


class SubmissionResponse(BaseModel):
    score: int
    total: int
