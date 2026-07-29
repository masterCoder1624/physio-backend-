from typing import List
from fastapi import HTTPException, status


class RoleChecker:
    """Dependency for role-based endpoint authorization."""

    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, payload: dict) -> bool:
        user_role = payload.get("role")
        if not user_role or user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current user role",
            )
        return True
