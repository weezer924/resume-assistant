from openai import AsyncOpenAI

from app.database import SqliteFactStore
from app.services.facts import Facts

DB_PATH = "database/resume_assistant.db"

from app.schema import ExtractionConfig
from app.services.fact_extraction import (
    PROMPT_ID,
    PROMPT_VERSION,
    OpenAIExtractor,
)

MODEL = "gpt-5-mini"

config = ExtractionConfig(
    model=MODEL,
    prompt_id=PROMPT_ID,
    prompt_version=PROMPT_VERSION,
)


def get_store() -> SqliteFactStore:
    return SqliteFactStore(DB_PATH)


def get_facts() -> Facts:
    return Facts(
        get_store(),
        OpenAIExtractor(AsyncOpenAI(), config.model),
        config.model,
        config.prompt_id,
        config.prompt_version,
    )
