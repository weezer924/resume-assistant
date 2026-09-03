## 20. Milestones and acceptance criteria

The schedule assumes at least 12 hours per week and owner-led implementation.

### Week 1 — Smallest structured-output vertical slice

Deliverable:

- one public synthetic career text fixture
- one Responses API call
- one Pydantic structured Fact output
- one locally saved Run record
- one inspectable CLI or minimal display of the result

Acceptance:

- The owner can explain request input, prompt, schema, response, validation, and persisted result.
- Invalid structured output produces a visible failure rather than silently continuing.
- Model and prompt identifiers are configuration, not buried in business logic.
- No RAG, Agent, or full UI is required yet.

### Week 2 — Document and provenance pipeline

Deliverable:

- DOCX, Markdown, and TXT parsing
- Document and immutable SourceSpan persistence
- candidate Fact extraction linked to SourceSpans

Acceptance:

- Paragraph and table-cell provenance can be inspected.
- Reimported unchanged content is detected by hash.
- Parse failures are explicit.
- SourceSpan text is never edited through Fact editing.

### Week 3 — Fact confirmation and JobRequirement extraction

Deliverable:

- Fact status workflow
- confirm/edit/reject UI
- pasted job input and structured requirements
- SQLite migrations

Acceptance:

- Pending and rejected Facts cannot enter generation eligibility.
- A user edit preserves original extraction and evidence.
- Job requirements have stable IDs and required/preferred classification.

### Week 4 — Retrieval baseline

Deliverable:

- rebuildable LanceDB projection
- vector, full-text, and hybrid retrieval modes
- initial Japanese retrieval set and hard negatives

Acceptance:

- Index rebuild from SQLite is documented and repeatable.
- Only confirmed Facts are retrieved by default.
- Retrieval candidates, scores, ranks, and selected Evidence IDs are persisted.
- The same cases compare vector-only, full-text-only, and hybrid results.

### Week 5 — Evidence-backed suggestion generation

Deliverable:

- bounded context builder
- structured Suggestion and Claim generation
- Evidence citations
- supported/clarification/development output separation

Acceptance:

- Each factual Claim cites valid confirmed evidence.
- A missing skill produces no fabricated experience.
- Context inputs and selection decisions are visible in the Run.
- Learning advice cannot appear in supported resume content.

### Week 6 — Deterministic evaluation baseline

Deliverable:

- public dataset of at least 12 high-value cases
- deterministic checker catalog
- local eval runner and case-level report

Acceptance:

- Each case exposes expected behavior, actual output, checker evidence, and final text.
- Hard-gate failures cannot be averaged away.
- The suite includes missing, conflicting, injection, and leakage cases.
- Normal CI runs without an OpenAI API key.

### Week 7 — Semantic judges and Run Detail

Deliverable:

- groundedness, relevance, exaggeration, and Japanese-quality judges
- versioned prompts
- complete Run Detail UI
- approximately 30 public cases

Acceptance:

- Judge outputs are structured and traceable to Claims and Evidence.
- At least two prompt or model configurations can be compared on the same cases.
- Run Detail shows prompt/model versions, tokens, latency, cost, retrieval, and checks.

### Week 8 — Bounded Evidence Agent

Deliverable:

- explicit deeper-investigation action
- read-only tools
- tool-call and turn limits
- structured Agent result and timeline

Acceptance:

- The Agent cannot mutate Facts or publish content.
- Required core checkers still run independently of the Agent.
- Tool calls and stop reason are inspectable.
- Tests cover repeated calls, missing evidence, conflicts, and limit exhaustion.

### Week 9 — Human calibration and safety pass

Deliverable:

- 15 human-labeled outputs
- judge calibration report
- adversarial and privacy review
- first private real-use suite

Acceptance:

- Confusion matrix, precision, recall, and disagreements are reported.
- At least one judge failure leads to a documented prompt, rubric, or product change.
- Private inputs and outputs are absent from Git status.
- Public reports contain only synthetic or sanitized data.

### Week 10 — Interview release

Deliverable:

- 40–60 public cases
- 10–20 private cases
- final sanitized evaluation report
- README, architecture explanation, local runbook, and demo script
- short recorded fallback demo

Acceptance:

- All hard release gates pass on the public release suite.
- A clean checkout follows documented local setup successfully.
- The owner can present the product, architecture, one success, two failures, and key trade-offs in ten minutes.
- Claims in public documentation match implemented evidence and do not imply multi-agent, OCR, fine-tuning, or production-scale deployment.

## 21. Demo narrative

The ten-minute interview demonstration follows this structure:

1. **Product problem — 1 minute:** tailoring a resume without unsupported claims.
2. **Primary workflow — 2 minutes:** import, confirm Facts, analyze a job, generate suggestions.
3. **Evidence and RAG — 2 minutes:** inspect selected evidence and retrieval scores.
4. **Reliability — 2 minutes:** show checkers, judges, and a failed unsupported-skill case.
5. **Agent — 1 minute:** run a bounded deeper investigation and inspect the tool timeline.
6. **Engineering trade-offs — 2 minutes:** explain SQLite/LanceDB, fixed pipeline versus Agent, local privacy, and excluded technologies.

## 22. Learning and collaboration protocol

Core implementation is owner-written.

For each ticket, assistance follows this sequence:

1. Provide one focused objective and the first useful command or observation point.
2. Let the owner inspect the complete output and explain their understanding.
3. Explain one data-flow or code concept at a time.
4. If blocked, provide progressively stronger hints.
5. Provide a small isolated example only when a hint is insufficient.
6. Review the owner's implementation against the Spec and acceptance criteria.
7. Provide a full implementation only after an explicit request.

Agent-generated work is not counted as owner practice. Boilerplate assistance must remain distinguishable from owner-implemented AI pipeline, retrieval, evaluation, and safety logic.

## 23. Deferred decisions

The following are intentionally deferred until representative data exists:

- exact OpenAI models for extraction, generation, judging, and Agent roles
- exact embedding model
- retrieval K values and score thresholds
- n-gram versus Lindera/IPADIC tokenizer choice
- reranker choice
- model retry policy by failure category
- soft-metric release thresholds
- OpenAI Agents SDK versus direct Responses function-tool loop for the bounded Agent

Each decision must be made from a fixed evaluation comparison rather than preference alone.

## 24. Specification approval checklist

Before implementation begins, confirm that:

- [ ] The product promise and target user are correct.
- [ ] Supported resume content, clarification, and development advice are clearly separated.
- [ ] Fact, Evidence, and Claim invariants are acceptable.
- [ ] Human confirmation is required before retrieval eligibility.
- [ ] The fixed pipeline and Evidence Agent boundaries are acceptable.
- [ ] SQLite is the source of truth and LanceDB is rebuildable.
- [ ] Evaluation cases and hard gates are sufficient.
- [ ] The UI and Run Detail scope are sufficient.
- [ ] Privacy and public-repository boundaries are acceptable.
- [ ] Non-goals are explicitly accepted.
- [ ] The 8–10 week milestones fit the available time.
- [ ] The owner-led learning protocol is accepted.

Implementation must not begin until this checklist is reviewed and the Spec status changes from **Draft for review** to **Approved**.
