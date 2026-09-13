## 20. Milestones and acceptance criteria

The schedule assumes at least 12 hours per week and owner-led implementation.

### Week 1 — Smallest structured-output vertical slice

Deliverable:

- one public synthetic career text fixture
- one Responses API call
- one Pydantic structured Fact output
- one locally saved Run record
- one inspectable minimal display of the result

Acceptance:

- The owner can explain request input, prompt, schema, response, validation, and persisted result.
    Anwser:
        
- Invalid structured output produces a visible failure rather than silently continuing.
- Model and prompt identifiers are configuration, not buried in business logic.
- No RAG, Agent, or full UI is required yet.

### Week 2 — Document and provenance pipeline

Deliverable:

- Markdown parsing
- Document and immutable SourceSpan persistence
- candidate Fact extraction linked to SourceSpans

Acceptance:

- Each candidate Fact can be traced to its persisted SourceSpan and exact source text.
- Existing SourceSpan text and sequence remain unchanged when parsing rules change.
- Empty or invalid UTF-8 input produces an explicit failure.
- SourceSpan text is never edited through Fact editing.

我把模型生成的声明和原始证据分开保存。来源编号由程序确定，原文片段在导入时固定下来，避免解析规则变化破坏历史溯源。模型输出出现问题时，可以找回当时使用的输入进行排查。

### Week 3 — Fact confirmation and JobRequirement extraction

Deliverable:

- Fact status workflow， add status to facts
- a connected import → extraction → confirm/edit/reject UI
- pasted job input and structured requirements
- SQLite migrations, update facts add status

Acceptance:

- Pending and rejected Facts cannot enter generation eligibility.
- A user edit preserves original extraction and evidence.
- The UI carries document and candidate identifiers through the workflow, displays source evidence and review status, and reports errors without requiring manual API calls.
- Job requirements have stable IDs and required/preferred classification.

- 待确认、已拒绝的 Fact 不能用于后续生成。
- 用户编辑不会丢失原始抽取和证据。
- 职位要求有稳定 ID，并标明 required / preferred。

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

你提供职位要求原文，LLM 提取结构化职位要求，根据各项要求，检索履历中已确认的 Fact＋对应 SourceSpan，LLM 根据检索到的证据，生成带引用的简历改进建议

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
- LangGraph graph with read-only tool nodes and a local checkpointer
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

### Week 10 — Portfolio release

Deliverable:

- a public evaluation suite covering the agreed core cases and observed failure modes, without a fixed case-count target
- private real-use cases when available, kept local and excluded from Git, without a fixed case-count target
- a final sanitized, reproducible evaluation report stating dataset coverage and limitations
- README, architecture explanation, local runbook, and demo script

Acceptance:

- All hard release gates pass on the public release suite.
- A clean checkout follows documented local setup successfully.
- The owner can present the product, architecture, one success, two failures, and key trade-offs in ten minutes.
- Claims in public documentation match implemented evidence and do not imply multi-agent, OCR, fine-tuning, or production-scale deployment.

## 21. Explicit non-goals

The 8–10 week release does not include:

- public hosted service
- user registration, OAuth, or multi-user authorization
- Gmail, Google Drive, or LinkedIn account integrations
- automatic website crawling
- scanned-document OCR
- image/VLM document understanding
- digital PDF support unless added after core completion
- autonomous Agent control of the core pipeline
- multi-agent systems
- MCP or A2A integration
- LangChain or LangGraph outside the Evidence Agent
- fine-tuning or model training
- self-improving or Meta Agent behavior
- open-ended autonomous exploration
- automatic job application submission
- full DOCX/PDF resume layout generation
- mobile-specific layout work
- public real-time API use
- conventional data-science model development or feature-engineering claims

## 22. Demo narrative

The ten-minute portfolio demonstration follows this structure:

1. **Product problem — 1 minute:** tailoring a resume without unsupported claims.
2. **Primary workflow — 2 minutes:** import, confirm Facts, analyze a job, generate suggestions.
3. **Evidence and RAG — 2 minutes:** inspect selected evidence and retrieval scores.
4. **Reliability — 2 minutes:** show checkers, judges, and a failed unsupported-skill case.
5. **Agent — 1 minute:** run a bounded deeper investigation and inspect the tool timeline.
6. **Engineering trade-offs — 2 minutes:** explain SQLite/LanceDB, fixed pipeline versus Agent, local privacy, and excluded technologies.

## 23. Learning and collaboration protocol

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

## 24. Deferred decisions

The following are intentionally deferred until representative data exists:

- exact OpenAI models for extraction, generation, judging, and Agent roles
- exact embedding model
- retrieval K values and score thresholds
- n-gram versus Lindera/IPADIC tokenizer choice
- reranker choice
- model retry policy by failure category
- soft-metric release thresholds
- whether the post-v1 Evidence Agent comparison uses the OpenAI Agents SDK or a direct Responses function-tool loop

Each decision must be made from a fixed evaluation comparison rather than preference alone.

## 25. Specification approval checklist

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
