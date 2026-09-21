from collections.abc import Awaitable, Callable

from app.database import SqliteStore
from app.schema import Job, ModelJobRequirementsOutput


class JobNotFound(Exception):
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

        requirements = await self.extractor(job)

        return requirements
