import re
from typing import Optional, Union
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.models.models import UserRoleEnum


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    role: Union[UserRoleEnum, str] = UserRoleEnum.PATIENT

    @model_validator(mode="before")
    @classmethod
    def resolve_names_and_role(cls, data: dict) -> dict:
        if isinstance(data, dict):
            full_name = data.get("full_name")
            first_name = data.get("first_name")
            last_name = data.get("last_name")

            if full_name and not (first_name and last_name):
                parts = full_name.strip().split(" ", 1)
                data["first_name"] = parts[0]
                data["last_name"] = parts[1] if len(parts) > 1 else ""
            elif first_name and not full_name:
                data["full_name"] = f"{first_name} {last_name}".strip() if last_name else first_name

            if not data.get("first_name"):
                data["first_name"] = "User"
            if data.get("last_name") is None:
                data["last_name"] = ""

            role = data.get("role")
            if role == "physio":
                data["role"] = UserRoleEnum.PHYSIOTHERAPIST
        return data

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token: Optional[str] = None  # Alias for access_token to support web client
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return UserRegisterRequest.validate_password_complexity(v)
