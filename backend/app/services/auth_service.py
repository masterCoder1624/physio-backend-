from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.schemas.user import UserUpdateRequest
from app.models.mongo_models import UserDocument


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.user_repo = UserRepository(db)

    async def register_user(self, req: UserRegisterRequest) -> Dict[str, Any]:
        """Register a new user after verifying email uniqueness in MongoDB."""
        existing = await self.user_repo.get_by_email(req.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        hashed_pwd = get_password_hash(req.password)
        role_val = req.role.value if hasattr(req.role, "value") else str(req.role)
        first_name = req.first_name or "User"
        last_name = req.last_name or ""
        user_dict = {
            "email": req.email.lower().strip(),
            "hashed_password": hashed_pwd,
            "first_name": first_name,
            "last_name": last_name,
            "phone": req.phone,
            "role": role_val,
            "is_active": True,
            "is_verified": False,
        }
        user = await self.user_repo.create(user_dict)
        full_name = f"{user.first_name} {user.last_name}".strip()
        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "id": user.id,
            "email": user.email,
            "full_name": full_name,
            "role": user.role,
        }

    async def login_user(self, req: UserLoginRequest) -> TokenResponse:
        """Authenticate user and generate JWT access and refresh tokens."""
        user = await self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        access_token = create_access_token(subject=user.id, role=role_str)
        refresh_token = create_refresh_token(subject=user.id)

        # Store refresh token in MongoDB
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.create_refresh_token(user.id, refresh_token, expires_at)

        full_name = f"{user.first_name} {user.last_name}".strip()
        return TokenResponse(
            access_token=access_token,
            token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            full_name=full_name,
            role=role_str,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Generate a new access token from a valid refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")
        db_token = await self.user_repo.get_refresh_token(refresh_token)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or invalid",
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        new_access_token = create_access_token(subject=user.id, role=role_str)
        full_name = f"{user.first_name} {user.last_name}".strip()
        return TokenResponse(
            access_token=new_access_token,
            token=new_access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            full_name=full_name,
            role=role_str,
        )

    async def update_profile(self, user_id: str, req: UserUpdateRequest) -> UserDocument:
        """Update only the authenticated user's editable profile fields."""
        updated = await self.user_repo.update(user_id, req.model_dump(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        return updated
