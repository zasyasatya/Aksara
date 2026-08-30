from pydantic import AliasChoices, Field
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

    # ── Mode aplikasi: "dev" atau "prod" ─────────────────────────────────
    # dev  → semua halaman dokumentasi selalu terlihat, login otomatis
    # prod → hanya halaman dokumentasi yang dipublikasikan admin yang terlihat
    #        (pengaturan via halaman Admin, butuh login admin)
    # Env: AKSARA_MODE (alias: MODE)
    mode: str = Field(default="dev", validation_alias=AliasChoices("AKSARA_MODE", "MODE", "mode"))

    # ── Autentikasi Admin (login username + password) ─────────────────────
    # Env: AKSARA_ADMIN_USERNAME / AKSARA_ADMIN_PASSWORD
    #      (alias: ADMIN_USERNAME / ADMIN_PASSWORD)
    admin_username: str = Field(
        default="admin",
        validation_alias=AliasChoices("AKSARA_ADMIN_USERNAME", "ADMIN_USERNAME", "admin_username"),
    )
    admin_password: str = Field(
        default="aksara-admin",
        validation_alias=AliasChoices("AKSARA_ADMIN_PASSWORD", "ADMIN_PASSWORD", "admin_password"),
    )

    # ── Autentikasi Guru (login username + password) ──────────────────────
    # Env: AKSARA_GURU_USERNAME / AKSARA_GURU_PASSWORD
    #      (alias: GURU_USERNAME / GURU_PASSWORD)
    guru_username: str = Field(
        default="guru",
        validation_alias=AliasChoices("AKSARA_GURU_USERNAME", "GURU_USERNAME", "guru_username"),
    )
    guru_password: str = Field(
        default="aksara-guru",
        validation_alias=AliasChoices("AKSARA_GURU_PASSWORD", "GURU_PASSWORD", "guru_password"),
    )

    class Config:
        env_file = ".env"

    @property
    def is_prod(self) -> bool:
        return self.mode.strip().lower() == "prod"

settings = Settings()
