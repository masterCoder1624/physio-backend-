import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection, db
from app.api.routes import auth_router, patients_router, payments_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("physioverse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for MongoDB Atlas connection management."""
    logger.info("Initializing MongoDB Atlas connection...")
    await connect_to_mongo()
    logger.info("MongoDB Atlas initialization complete.")
    yield
    logger.info("Closing MongoDB Atlas connection...")
    await close_mongo_connection()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PhysioVerse - Physiotherapy Patient Management System",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Custom Middlewares - Only in production
if settings.ENVIRONMENT == "production":
    from app.api.middleware.security import SecurityHeadersMiddleware, CorrelationIdMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

# CORS Configuration for Flutter Web (supports dynamic localhost ports like localhost:62227)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "N/A")
    logger.error(f"[{request.method}] [{request.url.path}] Global exception [Request ID: {correlation_id}]: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An internal server error occurred",
            "request_id": correlation_id,
        },
    )


# Health Check & MongoDB Atlas Readiness Probes
@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "ok",
        "message": "Server is running",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "mongodb_atlas",
    }


@app.get("/health/readiness", tags=["Health Check"])
async def readiness_check():
    try:
        if db.client is None:
            raise RuntimeError("MongoDB client is uninitialized")
        await db.client.admin.command("ping")
        return {
            "status": "ready",
            "database": "mongodb_atlas_connected",
        }
    except Exception as e:
        logger.error(f"MongoDB Atlas readiness probe failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "mongodb_atlas_disconnected",
                "error": str(e) if settings.DEBUG else "MongoDB connection failed",
            },
        )


# Include V1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(patients_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)