from openai import AsyncOpenAI

from app.schema import ModelFactsOutput, SourceSpan

FACT_PROMPT_ID = "fact_extraction"
FACT_PROMPT_VERSION = "2.0"  # updated whenever the prompt changes
FACT_PROMPT = (
    "Extract all factual resume claims from the supplied source span. "
    "Do not add information not present in the source. "
    "The evidence_quote must be copied exactly from the source."
)


class FactAIExtractor:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
    ) -> None:
        self.client: AsyncOpenAI = client
        self.model: str = model

    async def __call__(self, source_span: SourceSpan) -> ModelFactsOutput:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": FACT_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"section: {source_span['section']}\nbody: {source_span['body']}"
                    ),
                },
            ],
            text_format=ModelFactsOutput,
            store=False,
        )

        output = response.output_parsed

        if output is None:
            raise RuntimeError("Model did not return a fact draft")

        return output
