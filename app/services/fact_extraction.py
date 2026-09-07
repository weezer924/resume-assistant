from openai import AsyncOpenAI

from app.schema import ModelFactOutput, SourceSpan

PROMPT_ID = "fact_extraction"
PROMPT_VERSION = "1.0"  # updated whenever the prompt changes
PROMPT = (
    "Extract one factual resume claim from the supplied source span. "
    "Do not add information not present in the source. "
    "The evidence_quote must be copied exactly from the source."
)


class OpenAIExtractor:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
    ) -> None:
        self.client: AsyncOpenAI = client
        self.model: str = model
        self.prompt_id: str = PROMPT_ID
        self.prompt_version: str = PROMPT_VERSION

    async def __call__(self, source_span: SourceSpan) -> ModelFactOutput:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"section: {source_span['section']}\nbody: {source_span['body']}"
                    ),
                },
            ],
            text_format=ModelFactOutput,
            store=False,
        )

        output = response.output_parsed

        if output is None:
            raise RuntimeError("Model did not return a fact draft")

        return output
