from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ALIGNED_",
        extra="ignore"
    )

    APP_NAME: str = "AlignED API"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = True
    
    # AI & Model configs
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    FALLBACK_GEMINI_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"
    
    # Gap Engine settings
    SIMILARITY_THRESHOLD: float = 0.70
    
    # File Paths
    BENCHMARKS_FILE: Path = BASE_DIR / "data" / "role_benchmarks.json"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]

settings = Settings()

