import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    KFDA_API_KEY = os.getenv("KFDA_API_KEY")
    UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # CORS 설정
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000"
    ] if ENVIRONMENT == "development" else [
        FRONTEND_URL
    ]

settings = Settings()