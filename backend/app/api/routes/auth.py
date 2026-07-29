from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserResponse
from app.schemas.common import APIResponse
from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import UserDocument

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    result = await service.register_user(req)
    return APIResponse(message="User registered successfully", data=result)


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(req: UserLoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    result = await service.login_user(req)
    return APIResponse(message="Login successful", data=result)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(req: RefreshTokenRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_access_token(req.refresh_token)
    return APIResponse(message="Token refreshed successfully", data=result)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user: UserDocument = Depends(get_current_user)):
    return APIResponse(message="User profile retrieved", data=UserResponse.model_validate(current_user))
