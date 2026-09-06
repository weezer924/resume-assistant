from openai import AsyncOpenAI

from app.database import SqliteFactStore
from app.services.fact_extraction import OpenAIExtractor
from app.services.facts import Facts

DB_PATH = "database/resume_assistant.db"


def get_store() -> SqliteFactStore:
    return SqliteFactStore(DB_PATH)


def get_facts() -> Facts:
    return Facts(
        get_store(),
        OpenAIExtractor(AsyncOpenAI(), "gpt-5-mini"),
    )
