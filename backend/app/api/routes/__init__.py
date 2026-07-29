from app.api.routes.auth import router as auth_router
from app.api.routes.patients import router as patients_router
from app.api.routes.payments import router as payments_router

__all__ = ["auth_router", "patients_router", "payments_router"]
