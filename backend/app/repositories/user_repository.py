from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.mongo_models import UserDocument, RefreshTokenDocument
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserDocument]):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(UserDocument, db, collection_name="users")
        self.token_repo = BaseRepository(RefreshTokenDocument, db, collection_name="refresh_tokens")

    async def get_by_email(self, email: str) -> Optional[UserDocument]:
        """Fetch user document by email address."""
        clean_email = email.lower().strip()
        doc = await self.collection.find_one({"email": clean_email})
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def create_refresh_token(
        self, user_id: str, token: str, expires_at
    ) -> RefreshTokenDocument:
        """Store active refresh token document for user."""
        token_data = {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
            "is_revoked": False,
        }
        return await self.token_repo.create(token_data)

    async def get_refresh_token(self, token: str) -> Optional[RefreshTokenDocument]:
        """Fetch active refresh token document by token string."""
        doc = await self.token_repo.collection.find_one(
            {"token": token, "is_revoked": False}
        )
        if not doc:
            return None
        return self.token_repo._doc_to_model(doc)

    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token by marking it as revoked."""
        await self.token_repo.collection.update_one(
            {"token": token},
            {"$set": {"is_revoked": True}},
        )
