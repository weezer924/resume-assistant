## 9. Bounded Evidence Agent

Deferred until after the first release. The optional Agent investigates evidence
gaps using bounded, read-only tools. It cannot edit Facts or publish suggestions.
See the [Agent ADR](adr/ADR-0001-langgraph-first-for-evidence-agent.md).

## 10. RAG and retrieval

### 10.1 Storage responsibilities

SQLite is the source of truth. Any retrieval index is a rebuildable projection
with stable references back to Facts and SourceSpans.

### 10.2 Indexed content

Search confirmed claims and supporting excerpts. Include only metadata needed
for retrieval and provenance; retain stable Fact and evidence references.

### 10.3 Retrieval stages

1. Build a query from a JobRequirement.
2. Retrieve candidates using one baseline method.
3. Resolve references and check current confirmation state in SQLite.
4. Select bounded Top-K evidence for context.
5. Save IDs, scores, ranks, and selections for inspection.

Select the initial method at implementation time. Vector/full-text comparison,
hybrid fusion, and reranking are post-release experiments.

### 10.4 Japanese retrieval

Include Japanese requirements and source excerpts in fixed cases. Assess the
chosen method on these examples before adding tokenizer-specific work.

### 10.5 Retrieval evaluation

Cases identify relevant evidence and hard negatives. Report Recall@K on cases
with labeled relevant evidence; inspect missing-evidence and hard-negative
behavior separately. Record K and configuration so comparisons are repeatable.

## 11. Prompt and context engineering

### 11.1 Prompt roles

Separate prompts for Fact extraction, JobRequirement extraction, and generation.

### 11.2 Prompt rules

Treat imported content as untrusted data. Define sufficient evidence and
missing-evidence behavior. Use structured outputs and distinguish factual
content from stylistic rewriting.

### 11.3 Context assembly

Application code selects the requirement, confirmed Facts, and exact excerpts
under an explicit context budget. Save selected evidence IDs and any truncation
decision. The full corpus is not sent to every generation call.

### 11.4 Prompt versioning

Give prompts stable IDs and versions. Record actual model and prompt versions
per Run. Compare a baseline and one revision on fixed inputs with the same model;
retain outputs and report regressions as well as improvements.

## 12. Model integration

### 12.1 API boundary

Use the official OpenAI Python SDK, Responses API, and Pydantic structured
outputs. Application code owns orchestration and validation.

### 12.2 Model roles

Configure extraction and generation models outside business logic. Configure an
embedding model if the selected retrieval method needs one.

### 12.3 Required telemetry

Record input identity, actual model and prompt version, timing, status, structured
output, and error for each extraction or generation Run. Retrieval records expose
candidates and selections. Generic events, token/cost dashboards, and Agent
tracing are deferred. Personal model inputs and outputs remain in local storage,
not general logs.

## 13. Evaluation system

### 13.1 Dataset groups

Use a small, fixed synthetic dataset safe for Git. Personal cases are optional
and remain gitignored. Coverage and explainable findings determine sufficiency,
not a predetermined case count.

### 13.2 Required scenario categories

- supported experience
- missing evidence
- semantically similar but non-supporting evidence
- invalid evidence references
- pending or rejected evidence, including stale retrieval results
- unsupported expansion and instructions embedded in source text

### 13.3 Evaluation record

Each case includes input fixtures, expected behavior, relevant or forbidden
evidence IDs, actual output, retrieval results, deterministic checks, and human
assessment. Reports identify model, prompt, retrieval configuration, and code
revision, and expose failures and dataset limitations.

### 13.4 Deterministic checks

Validate output shape, reference existence, and current Fact confirmation state.
Every factual claim requires an evidence reference. Gap outputs stay separate
from supported resume content. A valid reference does not prove entailment.

### 13.5 Semantic assessment

The owner reviews whether evidence supports each generated claim and whether
rewriting adds unsupported details. Check job relevance and Japanese readability.
Automated LLM judges are a later extension.

### 13.6 Prompt comparison

Run a baseline and one revised prompt against the same fixed cases and model.
Report case-level differences and manual assessments. Small-sample stochastic
results are directional evidence, not a general quality guarantee.

### 13.7 Release gates

On the agreed release cases, resolve invalid citations, use of unconfirmed facts,
unsupported experience, and observed injection or privacy failures before release.
A retrieval score improvement cannot compensate for these failures. Publish the
coverage and limitations alongside the result.

### 13.8 CI policy

CI runs formatting, static checks, and deterministic unit/integration tests using
stubs. Live model evaluations run explicitly and produce local reports; normal
CI requires no OpenAI key. Verify the connected UI with synthetic data and stub
responses. Framework-specific frontend suites are deferred with migration.
