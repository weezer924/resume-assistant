from collections.abc import Awaitable, Callable

from app.database import SqliteStore
from app.schema import Job, ModelJobRequirementsOutput


class JobNotFound(Exception):
    pass


class RequirementNotInJob(Exception):
    pass


class Jobs:
    def __init__(
        self,
        store: SqliteStore,
        extractor: Callable[[Job], Awaitable[ModelJobRequirementsOutput]],
        model: str,
        prompt_id: str,
        prompt_version: str,
    ) -> None:
        self.store: SqliteStore = store
        self.extractor: Callable[[Job], Awaitable[ModelJobRequirementsOutput]] = (
            extractor
        )
        self.model: str = model
        self.prompt_id: str = prompt_id
        self.prompt_version: str = prompt_version

    async def extract(self, job_id: str) -> ModelJobRequirementsOutput:
        job = self.store.get_job(job_id)

        if job is None:
            raise JobNotFound(job_id)

        output = await self.extractor(job)

        for requirement in output.requirements:
            if requirement.requirement_text not in job.source_text:
                raise RequirementNotInJob(
                    "generate text is not found in the source text from job"
                )

        _ = self.store.save_job_requirements(job_id, output.requirements)

        return output
