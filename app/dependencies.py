import os
from pathlib import Path

from openai import AsyncOpenAI

from app.database import SqliteStore
from app.services.facts import Facts
from app.services.jobs import Jobs

DB_PATH = "database/resume_assistant.db"

from app.schema import ExtractionConfig
from app.services.fact_extraction import (
    FACT_PROMPT_ID,
    FACT_PROMPT_VERSION,
    FactAIExtractor,
)
from app.services.job_extraction import (
    JOB_PROMPT_ID,
    JOB_PROMPT_VERSION,
    JobAIExtractor,
)

MODEL = "gpt-5-mini"

fact_config = ExtractionConfig(
    model=MODEL,
    prompt_id=FACT_PROMPT_ID,
    prompt_version=FACT_PROMPT_VERSION,
)

job_config = ExtractionConfig(
    model=MODEL,
    prompt_id=JOB_PROMPT_ID,
    prompt_version=JOB_PROMPT_VERSION,
)


def get_store() -> SqliteStore:
    db_path = os.environ.get("RESUME_ASSISTANT_DB_PATH", DB_PATH)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return SqliteStore(db_path)


def get_facts_service() -> Facts:
    return Facts(
        get_store(),
        FactAIExtractor(AsyncOpenAI(), fact_config.model),
        fact_config.model,
        fact_config.prompt_id,
        fact_config.prompt_version,
    )


def get_job_requirements_service() -> Jobs:
    return Jobs(
        get_store(),
        JobAIExtractor(AsyncOpenAI(), job_config.model),
        job_config.model,
        job_config.prompt_id,
        job_config.prompt_version,
    )
