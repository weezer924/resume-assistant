from openai import AsyncOpenAI

client = AsyncOpenAI()

from app.schema import FactDraft, SourceSpan


async def extract_fact_draft(source_span: SourceSpan) -> FactDraft:
    response = await client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "developer",
                "content": (
                    "Extract one factual resume claim from the supplied source span. "
                    "Do not add information not present in the source. "
                    "The evidence_quote must be copied exactly from the source."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"source_sequence: {source_span['sequence']}\n"
                    f"section: {source_span['section']}\n"
                    f"text: {source_span['text']}"
                ),
            },
        ],
        text_format=FactDraft,
    )

    fact_draft = response.output_parsed

    if fact_draft is None:
        raise RuntimeError("Model did not return a fact draft")

    return fact_draft
