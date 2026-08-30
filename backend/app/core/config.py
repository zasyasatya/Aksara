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
    # dev  → semua halaman dokumentasi selalu terlihat, akses admin otomatis
    # prod → hanya halaman dokumentasi yang dipublikasikan admin yang terlihat
    #        (pengaturan via halaman Admin, butuh token admin)
    # Env: AKSARA_MODE (alias: MODE)
    mode: str = Field(default="dev", validation_alias=AliasChoices("AKSARA_MODE", "MODE", "mode"))
    # Token untuk autentikasi admin di mode prod (header X-Admin-Token).
    # Wajib diset via env AKSARA_ADMIN_TOKEN (alias: ADMIN_TOKEN) pada produksi.
    admin_token: str = Field(default="aksara-admin", validation_alias=AliasChoices("AKSARA_ADMIN_TOKEN", "ADMIN_TOKEN", "admin_token"))

    class Config:
        env_file = ".env"

    @property
    def is_prod(self) -> bool:
        return self.mode.strip().lower() == "prod"

settings = Settings()
