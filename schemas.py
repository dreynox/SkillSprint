from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    year: Optional[int] = None
    branch: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    year: Optional[int]
    branch: Optional[str]
    role: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
