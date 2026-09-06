from openai import AsyncOpenAI

from app.database import SqliteFactStore
from app.services.fact_extraction import OpenAIExtractor
from app.services.facts import Facts


def get_facts() -> Facts:
    return Facts(SqliteFactStore(), OpenAIExtractor(AsyncOpenAI(), "gpt-5-mini"))
