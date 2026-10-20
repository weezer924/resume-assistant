import time
from collections.abc import Awaitable, Callable

from app.database import SqliteStore
from app.schema import Job, JobRequirement, ModelJobRequirementsOutput, ModelJobRun


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

        start_at = time.time()

        try:
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

        except Exception as e:
            _ = self.store.save_model_job_run(
                self._run(job_id, start_at, "failed", None, f"{type(e).__name__}: {e}")
            )
            raise

        else:
            _ = self.store.save_model_job_run(
                self._run(job_id, start_at, "completed", output.model_dump_json(), None)
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

    def _run(
        self,
        job_id: str,
        start_at: float,
        status: str,
        output: str | None,
        error: str | None,
    ) -> ModelJobRun:
        return ModelJobRun(
            job_id=job_id,
            model=self.model,
            prompt_id=self.prompt_id,
            prompt_version=self.prompt_version,
            start_at=start_at,
            completed_at=time.time(),
            status=status,
            output=output,
            error=error,
        )
