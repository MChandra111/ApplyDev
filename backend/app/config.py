"""Shared configuration: environment variables and logging."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Repo root is two levels above backend/app (ApplyDev/)
_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_project_env() -> None:
    """Load `.env` from the monorepo root so scripts and the API share one file."""
    load_dotenv(_REPO_ROOT / ".env", override=False)


def get_repo_root() -> Path:
    """Return the monorepo root directory (ApplyDev/)."""
    return _REPO_ROOT


def get_documents_dir() -> Path:
    """Return the folder containing resume and project text files."""
    return _REPO_ROOT / "documents"


def get_env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable, or a default if it is unset."""
    return os.getenv(name, default)


def get_required_env(name: str) -> str:
    """Return an environment variable or raise a clear error if it is missing."""
    value = os.getenv(name)
    if not value:
        msg = f"Missing required environment variable: {name}. Check your .env file."
        raise RuntimeError(msg)
    return value


def configure_logging(level: int = logging.DEBUG) -> None:
    """Configure root logger so agent/tool DEBUG lines appear in the console."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def configure_langsmith() -> None:
    """Enable LangSmith tracing when LANGSMITH_API_KEY is set in .env."""
    load_project_env()
    api_key = get_env("LANGSMITH_API_KEY")
    if not api_key:
        logging.getLogger(__name__).info(
            "LangSmith tracing off (set LANGSMITH_API_KEY to enable)",
        )
        return

    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", api_key)
    os.environ.setdefault(
        "LANGCHAIN_PROJECT",
        get_env("LANGSMITH_PROJECT", "applydev") or "applydev",
    )
