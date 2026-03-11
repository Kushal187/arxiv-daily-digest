from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


_configure_logging()


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    worker_internal_token: str = os.getenv("WORKER_INTERNAL_TOKEN", "")
    ingest_job_token: str = os.getenv("INGEST_JOB_TOKEN", "")
    enable_paper_explain: bool = os.getenv("ENABLE_PAPER_EXPLAIN", "false").lower() == "true"
    summary_provider: str = os.getenv("SUMMARY_PROVIDER", "bedrock")
    summary_model: str = os.getenv("SUMMARY_MODEL", "qwen.qwen3-32b-v1:0")
    bedrock_region: str = os.getenv("BEDROCK_REGION", "us-east-1")
    bedrock_base_url: str = os.getenv("BEDROCK_BASE_URL", "")
    bedrock_api_key: str = os.getenv("BEDROCK_API_KEY", "")


settings = Settings()
