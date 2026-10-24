from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_PATH: str = "backend/data/shopledger.db"
    UPLOAD_DIR: str = "backend/data/uploads"
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def database_path_resolved(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent
        p = Path(self.DATABASE_PATH)
        if not p.is_absolute():
            p = base_dir / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def upload_dir_resolved(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            p = base_dir / p
        p.mkdir(parents=True, exist_ok=True)
        return p

settings = Settings()
