import os
from typing import List, Union
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Settings:
    # Project Info
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "PhysioVerse Backend SaaS")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # Render Deployment Keep-Alive Settings
    RENDER_BACKEND_URL: str = os.getenv(
        "RENDER_BACKEND_URL", "https://physioverse-backend.onrender.com"
    )

    # JWT / Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-this-in-production-physioverse-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # MongoDB Configuration (supporting both MONGODB_URL and MONGODB_URI)
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        os.getenv("MONGODB_URI", "mongodb+srv://priyanshu1624:priyanshu1624a@cluster0.h5tji.mongodb.net/?appName=Cluster0")
    )
    MONGODB_URI: str = MONGODB_URL
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "physioverse")

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5000",
    ]

    # Payment / Storage / Email
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "physioverse-media")

    def __init__(self):
        # Debug prints for verification
        print("\n" + "=" * 80)
        print("CONFIGURATION LOADED")
        print("=" * 80)
        print(f"✓ PROJECT_NAME: {self.PROJECT_NAME}")
        print(f"✓ ENVIRONMENT: {self.ENVIRONMENT}")
        print(f"✓ DEBUG: {self.DEBUG}")
        print(f"✓ RENDER_BACKEND_URL: {self.RENDER_BACKEND_URL}")
        print(f"✓ MongoDB URL (first 60 chars): {self.MONGODB_URL[:60]}...")
        print(f"✓ CORS Origins: {self.BACKEND_CORS_ORIGINS}")
        print("=" * 80 + "\n")


# Create singleton instance
settings = Settings()
