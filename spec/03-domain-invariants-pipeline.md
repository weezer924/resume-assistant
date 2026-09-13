## 7. Domain invariants / 业务规则

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

## 8. Fixed pipeline / 产品的完整处理顺序

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
