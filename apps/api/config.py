"""Runtime configuration. Environment variables use the ARTH_ prefix."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARTH_", env_file=str(ROOT / ".env"), extra="ignore")

    database_url: str = f"sqlite:///{(ROOT / 'database' / 'arthdarshan.db').as_posix()}"
    auto_migrate: bool = True
    low_resource: bool = False

    ollama_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen2.5:3b-instruct"
    llm_timeout: float = 25.0
    llm_enabled: bool = True

    enable_embeddings: bool = True
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    whisper_model: str = "base"
    piper_voices_dir: str = str(ROOT / "data" / "voices")

    scenarios_dir: str = str(ROOT / "configs" / "scenarios")
    knowledge_dir: str = str(ROOT / "data" / "knowledge_base")
    models_dir: str = str(ROOT / "ml" / "models")
    artifacts_dir: str = str(ROOT / "artifacts")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    log_level: str = "INFO"

    @property
    def llm_active(self) -> bool:
        return self.llm_enabled and not self.low_resource


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
