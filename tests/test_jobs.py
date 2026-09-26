from pathlib import Path

import pytest

from app.database import SqliteStore
from app.schema import Job, ModelJobRequirementOutput, ModelJobRequirementsOutput
from app.services.jobs import Jobs, RequirementLevelNotInJob, RequirementNotInJob


@pytest.fixture
def store(tmp_path: Path) -> SqliteStore:
    store = SqliteStore(str(tmp_path / "test.db"))

    job_id = "job-1"
    store.save_job(
        Job(
            id=job_id,
            source_text="Python experience is required.AWS experience is preferred.",
        )
    )

    return store


async def stub_requirements(_job: Job) -> ModelJobRequirementsOutput:
    return ModelJobRequirementsOutput(
        requirements=[
            ModelJobRequirementOutput(
                requirement_text="Python experience is required.",
                normalized_requirement="python experience",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            ),
            ModelJobRequirementOutput(
                requirement_text="AWS experience is preferred.",
                normalized_requirement="aws experience",
                category="technical_skill",
                required_or_preferred="preferred",
                years_or_level=None,
            ),
        ]
    )


async def stub_not_matched_requirements(_job: Job) -> ModelJobRequirementsOutput:
    return ModelJobRequirementsOutput(
        requirements=[
            ModelJobRequirementOutput(
                requirement_text="Python experience is required.",
                normalized_requirement="python experience",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            ),
            ModelJobRequirementOutput(
                requirement_text="Kubernetes experience is required.",
                normalized_requirement="Kubernetes experience",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            ),
        ]
    )


async def test_extract_job(store: SqliteStore):
    jobs = Jobs(store, stub_requirements, "model", "prompt_id", "prompt_version")
    output = await jobs.extract("job-1")

    assert len(output) == 2
    assert output[0].requirement_text == "Python experience is required."
    assert output[0].required_or_preferred == "required"
    assert output[1].requirement_text == "AWS experience is preferred."
    assert output[1].required_or_preferred == "preferred"


async def test_extract_job_requirement_not_in_job(store: SqliteStore):
    jobs = Jobs(
        store, stub_not_matched_requirements, "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(RequirementNotInJob):
        _ = await jobs.extract("job-1")

    assert store.get_job_requirements("job-1") == []


async def test_extract_job_rejects_level_not_in_requirement(store: SqliteStore):
    async def invented_level(_job: Job) -> ModelJobRequirementsOutput:
        return ModelJobRequirementsOutput(
            requirements=[
                ModelJobRequirementOutput(
                    requirement_text="Python experience is required.",
                    normalized_requirement="Python experience",
                    category="technical_skill",
                    required_or_preferred="required",
                    years_or_level="5 years",
                )
            ]
        )

    jobs = Jobs(store, invented_level, "model", "prompt_id", "prompt_version")

    with pytest.raises(RequirementLevelNotInJob):
        _ = await jobs.extract("job-1")

    assert store.get_job_requirements("job-1") == []


async def test_extract_job_preserves_explicit_level(store: SqliteStore):
    store.save_job(
        Job(id="job-2", source_text="5 years of Python experience required.")
    )

    async def explicit_level(_job: Job) -> ModelJobRequirementsOutput:
        return ModelJobRequirementsOutput(
            requirements=[
                ModelJobRequirementOutput(
                    requirement_text="5 years of Python experience required.",
                    normalized_requirement="Python experience",
                    category="technical_skill",
                    required_or_preferred="required",
                    years_or_level="5 years",
                )
            ]
        )

    jobs = Jobs(store, explicit_level, "model", "prompt_id", "prompt_version")

    requirements = await jobs.extract("job-2")

    assert requirements[0].years_or_level == "5 years"
    assert store.get_job_requirements("job-2") == requirements
