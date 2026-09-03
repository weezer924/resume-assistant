from app.database import SqliteFactStore
from app.services.fact_extraction import extract_fact_draft
from app.services.facts import Facts


def get_facts() -> Facts:
    return Facts(SqliteFactStore(), extract_fact_draft)
