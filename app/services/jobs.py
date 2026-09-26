from collections.abc import Awaitable, Callable

from app.database import SqliteStore
from app.schema import Job, JobRequirement, ModelJobRequirementsOutput


class JobNotFound(Exception):
    pass


class RequirementNotInJob(Exception):
    pass


class RequirementLevelNotInJob(Exception):
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

    async def extract(self, job_id: str) -> list[JobRequirement]:
        job = self.store.get_job(job_id)

        if job is None:
            raise JobNotFound(job_id)

        output = await self.extractor(job)

        for requirement in output.requirements:
            if requirement.requirement_text not in job.source_text:
                raise RequirementNotInJob(
                    "generate text is not found in the source text from job"
                )
            if requirement.years_or_level is not None and (
                not requirement.years_or_level.strip()
                or requirement.years_or_level not in requirement.requirement_text
            ):
                raise RequirementLevelNotInJob(
                    "years_or_level is not found in the requirement quote"
                )

        requirement_ids = self.store.save_job_requirements(job_id, output.requirements)
        return [
            JobRequirement(
                id=requirement_id,
                job_id=job_id,
                requirement_text=requirement.requirement_text,
                normalized_requirement=requirement.normalized_requirement,
                category=requirement.category,
                required_or_preferred=requirement.required_or_preferred,
                years_or_level=requirement.years_or_level,
            )
            for requirement_id, requirement in zip(
                requirement_ids, output.requirements, strict=True
            )
        ]
