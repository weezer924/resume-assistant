from openai import AsyncOpenAI

from app.schema import ModelFactOutput, SourceSpan


class OpenAIExtractor:
    def __init__(
        self,
        openAI: AsyncOpenAI,
        model: str,
    ) -> None:
        self.client: AsyncOpenAI = openAI
        self.model: str = model

    async def __call__(self, source_span: SourceSpan) -> ModelFactOutput:
        response = await self.client.responses.parse(
            model=self.model,
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
