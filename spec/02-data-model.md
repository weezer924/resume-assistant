## 6. Domain model

### 6.1 Model relationships

```text
Document
  └── SourceSpan
        └── FactEvidence
              └── Fact

Job
  └── JobRequirement

JobRequirement
  └── RetrievalCandidate
        └── Fact / SourceSpan

Suggestion
  └── Claim
        └── ClaimEvidence
              └── FactEvidence

Run
  └── RunStep / RunEvent
```

### 6.2 Document

Represents one imported local source.

Required fields:

| Field | Description |
| --- | --- |
| `id` | Stable internal identifier |
| `document_type` | Resume, LinkedIn export, project note, or other supported source |
| `original_filename` | Local display name; excluded from public artifacts when sensitive |
| `content_hash` | Detects duplicate or changed imports |
| `parser_name` | Parser used for extraction |
| `parser_version` | Version used for reproducibility |
| `imported_at` | Import timestamp |
| `local_path_ref` | Optional local-only reference; never exported publicly |
| `status` | Imported, parsed, failed, or deleted |

### 6.3 SourceSpan

An immutable piece of source text with a stable location.

Required fields:

| Field | Description |
| --- | --- |
| `id` | Evidence-facing stable identifier |
| `document_id` | Parent document |
| `body` | Exact extracted source text |
| `section` | Heading or logical section when known |
| `location_type` | Paragraph, table cell, line range, or other supported locator |
| `location_data` | Structured coordinates within the source |
| `sequence` | Stable order in the parsed document |
| `body_hash` | Detects source changes |

SourceSpan text is never edited. Corrections create or update Facts, not source excerpts.

### 6.4 Fact

A normalized, human-reviewable career fact.

Common fields:

| Field | Description |
| --- | --- |
| `id` | Stable Fact ID |
| `fact_type` | Typed category |
| `summary` | Normalized factual statement |
| `organization` | Related organization when supported |
| `project` | Related project when supported |
| `start_date` | Optional supported start date |
| `end_date` | Optional supported end date |
| `skills` | Supported technologies or competencies |
| `attributes` | Fact-type-specific validated fields |
| `status` | Pending, confirmed, rejected, or conflicting |
| `created_at` | Creation timestamp |
| `updated_at` | Last modification timestamp |
| `confirmed_at` | Human confirmation timestamp |

Initial Fact types:

- `employment`
- `project`
- `responsibility`
- `achievement`
- `technology_experience`
- `language`
- `education`
- `certification`

Each type shares the common fields and validates its own `attributes` structure.

### 6.5 FactEvidence

Many-to-many relationship between Facts and SourceSpans.

Required fields:

- `fact_id`
- `source_span_id`
- `support_type`: direct, partial, conflicting, or contextual
- `extraction_run_id`
- `created_at`

### 6.6 Job and JobRequirement

Job fields include a stable ID, source text, source hash, language, import time, and extraction version.

JobRequirement fields include:

- `id`
- `job_id`
- `category`
- `requirement_text`
- `normalized_requirement`
- `required_or_preferred`
- `years_or_level`, when explicitly stated

`JobRequirement.priority` and `JobRequirement.status` are deferred until a concrete consumer requires them. This does not defer the Fact review status workflow.

### 6.7 RetrievalCandidate

Captures retrieval evidence before generation.

Required fields:

- `run_id`
- `requirement_id`
- `fact_id`
- `source_span_id`
- vector distance or similarity
- full-text score
- fused score
- reranker score, when used
- retrieval rank
- retrieval method and version
- selected-for-context flag

Scores are diagnostic signals, not natural-language explanations and not proof by themselves.

### 6.8 Suggestion and Claim

A Suggestion represents one proposed change to resume content. A Suggestion may contain one or more atomic Claims.

Suggestion fields include:

- original content
- proposed content
- related Requirement IDs
- final status
- user action
- user-edited content
- optional edit reason

Claim fields include:

- `id`
- `suggestion_id`
- atomic claim text
- claim type
- cited Evidence IDs
- deterministic result
- groundedness result
- exaggeration result
- publishability status

Every factual Claim requires at least one valid Evidence ID. Stylistic glue may be uncited only when it introduces no new factual content.

### 6.9 Run, RunStep, and RunEvent

A Run is the reproducibility boundary for one pipeline or evaluation execution.

Run metadata includes:

- run type
- source document hashes
- job hash
- Git commit SHA, when available
- prompt IDs, versions, and hashes
- model roles and model identifiers
- schema versions
- retrieval configuration
- started/completed timestamps
- final status
- token usage
- latency
- estimated cost
- error summary

RunSteps represent fixed pipeline stages. RunEvents represent model calls, tool calls, tool results, checks, state transitions, and structured stop reasons.

Raw hidden model reasoning is never stored or displayed.

Business rules and execution responsibilities are defined in [Domain invariants and fixed pipeline](03-domain-invariants-pipeline.md).
