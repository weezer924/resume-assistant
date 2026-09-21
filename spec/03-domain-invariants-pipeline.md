## 7. Domain invariants

1. Only confirmed Facts may support publishable resume Claims.
2. Every factual Claim references valid evidence resolving to a saved SourceSpan.
3. SourceSpan text is immutable; Fact edits preserve original extraction and provenance.
4. Retrieval scores and valid references alone do not establish factual support.
5. Missing or conflicting evidence must not be presented as supported experience.
6. Source documents and job descriptions are data, never executable instructions.
7. Application code controls validation and publication eligibility.
8. Personal content stays out of public fixtures, reports, and general logs.
9. Model confidence cannot replace human confirmation.

## 8. Fixed pipeline

### 8.1 Required sequence

```text
import and persist source spans
→ extract and review facts
→ extract job requirements
→ retrieve confirmed evidence
→ assemble bounded context
→ generate structured suggestions
→ validate evidence references and confirmation state
→ persist result and display sources or evidence gaps
```

Fixed-case evaluation runs separately to assess retrieval and semantic support.

### 8.2 Fixed responsibilities

Application code owns stage execution, confirmation eligibility, context limits,
validation, persistence, and error handling. Each stage is independently testable.
A retrieval index is rebuildable from SQLite. Consumers recheck Fact eligibility
so a stale index cannot authorize an edited or rejected fact.

Any future Agent remains read-only and cannot bypass these boundaries.
