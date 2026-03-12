import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

try:
    # Optional fallback to existing keys module if present.
    from api_keys import (
        openai_api_key as _OPENAI_FALLBACK,
        fda_api_key as _FDA_FALLBACK,
        ncbi_api_key as _NCBI_FALLBACK,
        ncbi_email as _NCBI_EMAIL_FALLBACK,
    )
except Exception:  # pragma: no cover - best-effort fallback
    _OPENAI_FALLBACK = None
    _FDA_FALLBACK = None
    _NCBI_FALLBACK = None
    _NCBI_EMAIL_FALLBACK = None


@dataclass
class Config:
    openai_api_key: Optional[str]
    fda_api_key: Optional[str]
    ncbi_email: Optional[str]
    ncbi_api_key: Optional[str]
    run_optimizer: bool
    lm_model: str


def load_config() -> Config:
    """Load configuration from .env and environment variables."""
    load_dotenv()

    openai_key = os.getenv("OPENAI_API_KEY") or _OPENAI_FALLBACK
    fda_key = os.getenv("FDA_API_KEY") or _FDA_FALLBACK
    ncbi_email = os.getenv("NCBI_EMAIL") or _NCBI_EMAIL_FALLBACK
    ncbi_key = os.getenv("NCBI_API_KEY") or _NCBI_FALLBACK

    run_optimizer_str = os.getenv("RUN_OPTIMIZER", "false").lower()
    run_optimizer = run_optimizer_str in {"1", "true", "yes", "on"}

    lm_model = os.getenv("DSPY_LM_MODEL", "openai/gpt-4o")

    return Config(
        openai_api_key=openai_key,
        fda_api_key=fda_key,
        ncbi_email=ncbi_email,
        ncbi_api_key=ncbi_key,
        run_optimizer=run_optimizer,
        lm_model=lm_model,
    )

