import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Conferência de Processos de Pagamento"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Storage & DB
    DATABASE_URL: str = "sqlite:///./processos.db"
    
    # Upload limits & rules
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_CONTENT_TYPES: list[str] = ["application/pdf"]
    
    # OCR Settings
    SCANNED_PAGE_CHAR_THRESHOLD: int = 50  # pages with fewer chars trigger OCR / warning
    TESSERACT_LANG: str = "por+eng"
    TESSERACT_PATH: str | None = None  # Auto-detected if in PATH or common Windows paths
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR: Path = BASE_DIR / "temp"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
