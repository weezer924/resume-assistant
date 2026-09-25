from openai import AsyncOpenAI

from app.schema import Job, ModelJobRequirementsOutput

JOB_PROMPT_ID = "job_extraction"
JOB_PROMPT_VERSION = "1.0"  # updated whenever the prompt changes
JOB_PROMPT = (
    "Extract all requirements from the supplied job requirements. "
    "Do not add information not present in the source. "
    "The requirement_text must be copied exactly from the job requirement description."
)


class JobAIExtractor:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
    ) -> None:
        self.client: AsyncOpenAI = client
        self.model: str = model

    async def __call__(self, job: Job) -> ModelJobRequirementsOutput:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "developer", "content": JOB_PROMPT},
                {"role": "user", "content": job.source_text},
            ],
            text_format=ModelJobRequirementsOutput,
            store=False,
        )

        output = response.output_parsed

        if output is None:
            raise RuntimeError("Model did not return a job requirement output")

        return output
