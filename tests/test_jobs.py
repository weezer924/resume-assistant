from pathlib import Path

import pytest

from app.database import SqliteStore
from app.schema import Job, ModelJobRequirementOutput, ModelJobRequirementsOutput
from app.services.jobs import Jobs, RequirementNotInJob


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
                requirement_text="Kubernetes experience is required.",
                normalized_requirement="Kubernetes experience",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            )
        ]
    )


async def test_extract_job(store: SqliteStore):
    jobs = Jobs(store, stub_requirements)
    output = await jobs.extract("job-1")

    assert len(output.requirements) == 2
    assert output.requirements[0].requirement_text == "Python experience is required."
    assert output.requirements[0].required_or_preferred == "required"
    assert output.requirements[1].requirement_text == "AWS experience is preferred."
    assert output.requirements[1].required_or_preferred == "preferred"


async def test_extract_job_requirement_not_in_job(store: SqliteStore):
    jobs = Jobs(store, stub_not_matched_requirements)

    with pytest.raises(RequirementNotInJob):
        _ = await jobs.extract("job-1")
