from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "PriStilo - Vitrine Virtual"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="sqlite:///./vitrine_virtual.db",
        description=(
            "Use postgresql+psycopg://user:password@host:5432/dbname in production."
        ),
    )
    seed_demo_data: bool = True

    consultant_whatsapp_number: str = Field(
        default="",
        description="Numero da consultora em formato internacional, ex: 5511999999999.",
    )
    public_store_url: str = ""
    upload_root: str = Field(
        default=str(BACKEND_DIR / "frontend" / "uploads"),
        description="Diretorio onde uploads ficam armazenados.",
    )

    admin_password: str = Field(
        default="",
        description="Senha exigida para acessar o painel administrativo.",
    )
    admin_session_secret: str = Field(
        default="",
        description="Segredo opcional para assinar o cookie de sessao administrativa.",
    )
    admin_session_cookie_name: str = "pristilo_admin_session"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    enable_ollama: bool = False

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
