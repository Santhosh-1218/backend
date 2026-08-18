import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "StockFlow - Smart Warehouse Operations")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "stockflow-1336b")
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "AIzaSyB26fG1gEDQJX3zZmLcAqbFM4FkmbfEUo8")
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://frontend-cuy3.vercel.app",
        "*"
    ]

settings = Settings()
