## 6. Domain model

The model separates source text, reviewed career facts, job requirements, and
generated claims. This preserves the evidence behind a statement as it moves
from extraction to human review and resume generation.

Implementation scope and delivery order are tracked in
[milestones](08-milestones-acceptance-criteria.md); design decisions are recorded
in the [model alignment ADR](adr/week3-model-alignment.md).

### 6.1 Model relationships

The source and review model uses these relationships:

```text
Document ──< SourceSpan ──< Fact
                              │
                              └── extraction_run_id → Run
```

A document contains ordered source spans. One extraction can produce several
facts from a span. Each fact has its own stable ID and review state.

The conceptual retrieval and generation model extends this flow (association
tables are optional until multiple sources require them):

```text
Job ──< JobRequirement ──< RetrievalCandidate >── Fact
Fact ──< FactEvidence >── SourceSpan
Suggestion ──< Claim ──< ClaimEvidence >── FactEvidence
```

### 6.2 Document

An imported career document, preserving the original text.

| Field | Meaning |
| --- | --- |
| `document_id` | Application-generated UUID |
| `filename` | Imported filename |
| `content` | Original document text |

The database also records `created_at`. A document and its source spans are
saved in one transaction.

### 6.3 SourceSpan

An immutable section of a document used as extraction input and source evidence.

| Field | Meaning |
| --- | --- |
| `section` | Heading text without Markdown markers |
| `level` | Heading level; 0 for text before the first heading |
| `body` | Original section text |
| `sequence` | One-based position within the document |

The database associates each span with its `document_id` and records an internal
`id` and `created_at`. Application lookups use `(document_id, sequence)`.

The Markdown parser splits on level-one and level-two headings. Deeper headings
remain in the section body. Extraction reads saved spans, so parser changes do
not alter existing evidence.

### 6.4 Fact

A career statement extracted from a source span and reviewed by the user.
The Python record model is named `FactDraft` for all three review states.

| Field | Meaning |
| --- | --- |
| `id` | Stable integer ID |
| `document_id` | Source document |
| `source_sequence` | Source span within that document |
| `claim` | Current editable statement |
| `original_claim` | Original extracted statement |
| `evidence_quote` | Verbatim quote from the source span |
| `status` | `pending`, `confirmed`, or `rejected` |
| `extraction_run_id` | Extraction Run ID; nullable when historical linkage is unavailable |
| `created_at` | Creation time |
| `updated_at` | Most recent update time |
| `confirmed_at` | Confirmation time; null when unconfirmed or historically unknown |

The model returns `ModelFactsOutput`, containing a list of `ModelFactOutput`
objects with only `claim` and `evidence_quote`. Application code validates each
quote against the selected span and assigns identity, provenance, and state.
Quote validation establishes that the excerpt exists; human review checks
whether it supports the statement.

| Action | Result |
| --- | --- |
| Extract | Create pending facts with independent IDs |
| Confirm pending fact | Mark confirmed and record confirmation time |
| Edit claim | Return to pending and clear confirmation time |
| Reject | Mark rejected and clear confirmation time |
| Repeat confirm or reject | Return the existing record unchanged |

Editing preserves the ID, original claim, quote, source, and extraction Run.
A rejected fact must be edited back to pending before confirmation. Only
confirmed facts are eligible to support retrieval and generation.

### 6.5 FactEvidence

Fact evidence is represented by the Fact's `document_id`, `source_sequence`,
`evidence_quote`, and `extraction_run_id`.

The planned `FactEvidence` association supports multiple source spans per fact
and distinguishes direct, partial, conflicting, and contextual support. The first
release can use stable references to the existing single-source
association without introducing this table.

### 6.6 Job and JobRequirement

A Job preserves the pasted job description.

| Field | Meaning |
| --- | --- |
| `id` | Stable application-generated ID |
| `source_text` | Original job description |

JobRequirement is the planned structured representation of an individual
requirement extracted from a Job.

| Field | Meaning |
| --- | --- |
| `id` | Stable requirement ID |
| `job_id` | Parent Job |
| `requirement_text` | Supporting quote from the job description |
| `normalized_requirement` | Normalized requirement statement |
| `category` | Requirement category |
| `required_or_preferred` | `required`, `preferred` |
| `years_or_level` | Explicitly stated experience or proficiency; otherwise absent |

Application code validates the supporting quote against the saved job text.
Extraction configuration belongs to the Run that produced the requirements.

### 6.7 RetrievalCandidate

A planned record linking a job requirement to a retrieved fact and its evidence.
It captures ranking scores, retrieval method, and whether the candidate was
selected for generation context.

Retrieval scores measure relevance; they do not establish factual support.

### 6.8 Suggestion and Claim

A planned Suggestion represents a proposed resume edit and its related job
requirements. User accept/edit/reject decisions and edit history are later
extensions.

A Claim is an atomic factual statement within a Suggestion. Each factual Claim
must cite valid evidence and pass validation before publication. Wording that
introduces no factual content does not require a citation.

### 6.9 Run, RunStep, and RunEvent

A Run records one execution and the configuration, result, or error needed to
inspect it. Fact extraction uses `ModelFactRun`:

| Fields | Meaning |
| --- | --- |
| `document_id`, `source_sequence` | Input source span |
| `model`, `prompt_id`, `prompt_version` | Actual extraction configuration |
| `start_at`, `completed_at` | Execution timestamps |
| `status` | `completed` or `failed` |
| `output` | Serialized structured model output |
| `error` | Failure details |

The database assigns the Run's `id` and `created_at`. Extracted facts reference
that ID. A completed extraction means model output and quote validation
succeeded; it does not mean the user confirmed the facts.

Job extraction Runs will identify the input Job. Planned RunSteps describe
pipeline stages, while RunEvents capture model calls, tool calls, checks, and
stop reasons. Hidden model reasoning is not stored.

Business rules and execution responsibilities are defined in
[Domain invariants and fixed pipeline](03-domain-invariants-pipeline.md).
