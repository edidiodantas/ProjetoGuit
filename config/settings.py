"""Environment-based application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env before building settings so local overrides are available.
load_dotenv()


def _split_origins(origins: str | None) -> list[str]:
    """Split a comma-separated CORS string into a clean list."""
    if not origins:
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables.

    Keeping config in one place makes the FastAPI app declarative and
    easy to inspect in tests.
    """

    # Kimi / Moonshot API
    # Uma chave free-tier de https://platform.moonshot.cn/ é suficiente para
    # estudantes e projetos pequenos. O modelo padrão "kimi-k2.5-lite" é o
    # indicado para economizar no plano gratuito; use outro modelo via .env se
    # tiver créditos pagos.
    kimi_api_key: str | None = field(default_factory=lambda: os.getenv("KIMI_API_KEY"))
    kimi_base_url: str = field(
        default_factory=lambda: os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    )
    # Modelo padrão do Kimi/Moonshot. "kimi-k2.5-lite" é a opção indicada para o
    # tier gratuito e pequenas tarefas de código. Pode ser substituído via .env.
    kimi_model: str = field(default_factory=lambda: os.getenv("KIMI_MODEL", "kimi-k2.5-lite"))

    # Server
    app_host: str = field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    app_port: int = field(
        default_factory=lambda: int(os.getenv("APP_PORT", "8000"))
    )

    # Security / limits
    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(os.getenv("CORS_ORIGINS"))
    )
    max_code_chars: int = field(
        default_factory=lambda: int(os.getenv("MAX_CODE_CHARS", "32000"))
    )
    kimi_request_timeout: float = field(
        default_factory=lambda: float(os.getenv("KIMI_REQUEST_TIMEOUT", "60"))
    )


def get_settings() -> Settings:
    """Return a fresh settings instance (handy for re-loading in tests)."""
    return Settings()
