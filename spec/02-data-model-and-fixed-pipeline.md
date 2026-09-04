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
| `extraction_confidence` | Model-reported extraction confidence; not trust status |
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
- `priority`
- `years_or_level`, when explicitly stated
- `status`

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

## 7. Domain invariants

The following rules are non-negotiable system invariants:

1. Only `confirmed` Facts may support publishable resume Claims.
2. Every factual Claim must reference valid Evidence IDs.
3. Every referenced Evidence ID must resolve to an existing SourceSpan through FactEvidence.
4. SourceSpan text is immutable after import.
5. Retrieval score alone never establishes factual support.
6. A skill-development suggestion can never become supported resume content automatically.
7. Missing evidence never becomes a factual negative claim; the system reports only that no evidence was found.
8. Conflicting evidence prevents automatic publication of affected Claims.
9. The Evidence Agent cannot mutate Facts, Evidence, Suggestions, or confirmation state.
10. Deterministic checks and publishing gates cannot be skipped by the Agent or generation model.
11. Personal content cannot appear in public fixtures, committed run outputs, or logs.
12. Model confidence cannot replace human confirmation.

## 8. Fixed pipeline

### 8.1 Required sequence

```text
parse local source
→ create SourceSpans
→ extract candidate Facts
→ human confirmation
→ rebuild retrieval projection
→ extract JobRequirements
→ retrieve and rerank evidence
→ assemble bounded context
→ generate structured Suggestions and Claims
→ run deterministic checks
→ run semantic judges
→ apply publishing gate
→ persist Run and display results
```

### 8.2 Fixed responsibilities

Application code, not an Agent, determines:

- which mandatory stages execute
- confirmation eligibility
- context size limits
- deterministic checks
- judge invocation policy
- publishing gate behavior
- persistence and audit behavior
- retry limits for required model calls

Each stage must be callable and testable independently.

