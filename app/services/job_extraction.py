from openai import AsyncOpenAI

from app.schema import Job, ModelJobRequirementsOutput

JOB_PROMPT_ID = "job_extraction"
JOB_PROMPT_VERSION = "1.1"  # updated whenever the prompt changes
JOB_PROMPT = (
    "Extract requirements explicitly marked as required or preferred from the job description. "
    "Do not infer a label; omit requirements without an explicit required or preferred label. "
    "Do not add information not present in the source. "
    "Copy requirement_text exactly from the job description. "
    "Set years_or_level to the exact words in requirement_text only when a year count "
    "or proficiency level is explicitly stated; otherwise set it to null."
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
