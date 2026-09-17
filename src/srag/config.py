from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, overridable with S_RAG_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="S_RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_host: str = "http://127.0.0.1:11434"
    generation_model: str = "qwen3:4b"
    embedding_model: str = "qwen3-embedding:0.6b"
    chunk_size_tokens: int = Field(default=600, ge=100, le=2000)
    chunk_overlap_tokens: int = Field(default=80, ge=0, le=500)
    default_top_k: int = Field(default=4, ge=1, le=20)
    generation_context_tokens: int = Field(default=4096, ge=2048, le=32768)
    max_output_tokens: int = Field(default=512, ge=64, le=2048)
    max_file_size_mb: int = Field(default=25, ge=1, le=500)
    typesafe_enabled: bool = False
    typesafe_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("TYPESAFE_API_KEY", "S_RAG_TYPESAFE_API_KEY"),
    )
    typesafe_model: str = "jev-latest"
    typesafe_candidate_top_k: int = Field(default=12, ge=1, le=20)
    typesafe_max_workers: int = Field(default=4, ge=1, le=8)
    typesafe_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    data_dir: Path = Path("data")
    artifacts_dir: Path = Path("artifacts")
    index_dir: Path = Path("indexes/default")
    handoff_dir: Path = Path("artifacts/handoffproof")


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".htm",
    ".txt",
    ".md",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".eml",
    ".msg",
    ".odt",
    ".ods",
    ".odp",
}
