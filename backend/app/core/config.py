from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "Aksara - Balinese Script Learning Platform"
    version: str = "1.0.0"
    description: str = "Platform belajar Aksara Bali dengan transliterasi canggih"
    api_prefix: str = "/api"
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://aksara.bali",
        "https://*.vercel.app",
    ]
    max_text_length: int = 5000
    rate_limit_per_minute: int = 60
    dictionary_enabled: bool = True
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
