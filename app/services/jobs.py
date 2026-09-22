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
    ) -> None:
        self.store: SqliteStore = store
        self.extractor: Callable[[Job], Awaitable[ModelJobRequirementsOutput]] = (
            extractor
        )

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

        return output
