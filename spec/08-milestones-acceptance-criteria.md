## 19. Milestones and acceptance criteria

The first release is a local, evidence-backed RAG workflow that can be run,
evaluated, and explained in a short demo. Project time is capped at five hours
per week. Weeks 1–3 record the elapsed project weeks. New work starts in Week 4.
Weeks 4–8 are the revised weekly targets, subject to the two-week reviews.
Review actual progress every two weeks and revise the forecast or scope.

### Progress snapshot — 2026-09-21

| Week | Deliverable | Status | Remaining |
| --- | --- | --- | --- |
| 1 | Structured extraction and Run record | Complete | Preserve completed scope |
| 2 | Document import and persisted provenance | Complete | Preserve completed scope |
| 3 | Fact review and initial Job schema | Closed; incomplete work carried forward | JD workflow and confirmed-only reads moved to Week 4 |
| 4 | Job analysis and confirmed-only reads | Next | JD persistence/extraction/UI and eligibility query |
| 5 | One retrieval baseline | Planned | Retrieval, evidence selection, fixed-case assessment |
| 6 | Evidence-backed suggestions | Planned | Context, generation, reference checks, gap display |
| 7 | Fixed-case evaluation and prompt comparison | Planned | Reproducible cases, comparison, report |
| 8 | Portfolio release | Planned | Setup verification, README, demo |

Three project weeks have elapsed. Weeks 1–2 met their agreed scope; Week 3
completed Fact review and the Job schema, while the remaining work moves to
Week 4. Closing the week does not count its unfinished requirements as completed.

The revised plan has **five weeks remaining (Weeks 4–8)**, targeting release at
the end of Week 8. At the five-hour weekly cap, this allocates up to **25 hours**
of owner time. This is a planning budget, not a measured effort estimate or a
completion guarantee. Reforecast after Weeks 4–5 using actual progress.

### Week 1 — Structured extraction and Run record · complete

- [x] Synthetic career input and a structured model response.
- [x] Configured model/prompt identifiers and a saved extraction Run.
- [x] Inspectable results and explicit invalid-output failures.

Accepted scope is retained; optional metadata does not reopen this milestone.

### Week 2 — Document and provenance pipeline · complete

- [x] Markdown import and immutable SourceSpan persistence.
- [x] Document and spans saved together.
- [x] Extraction reads saved spans and validates exact source quotes.
- [x] Empty or invalid UTF-8 input produces an explicit error.

Accepted scope is retained; parser expansion is outside the first release.

### Week 3 — Fact review and initial Job schema · closed

Completed:

- [x] Persist pending candidates with stable IDs and extraction Run links.
- [x] Extract multiple Facts per span and review each independently.
- [x] Confirm/edit/reject the same Fact, preserving original claim and provenance.
- [x] Connected import → extract → review UI and API integration tests.
- [x] Minimal Job schema: `id` and `source_text`.

Carried forward: the JD workflow and confirmed-only reads below were not
completed in Week 3. Migration practice remains deferred beyond the first release.

### Week 4 — Job analysis and confirmed-only reads · next

- [x] Save pasted JD text and read it back by stable Job ID.
- [x] Extract and persist requirements with stable IDs and validated source quotes.
- [x] Classify required/preferred; preserve only explicit levels.
- [ ] Record successful and failed extraction Runs against the actual Job input.
- [ ] Connect pasted JD input and requirement inspection to the HTML UI.
- [ ] Verify usable-fact reads exclude pending and rejected records.

Done when a synthetic JD can be pasted, saved, extracted, and inspected with
visible errors, and confirmed-only reads are verified. Migration practice is
deferred, not completed. Next slice: save and retrieve a Job before adding LLM
extraction.

### Week 5 — One retrieval baseline (RAG) · planned

- [ ] Query confirmed Facts for a JobRequirement using one retrieval method.
- [ ] Return bounded Top-K results with stable evidence references and excerpts.
- [ ] Record candidate IDs, scores, ranks, and selected evidence.
- [ ] Recheck current confirmation state in SQLite when consuming results.
- [ ] Inspect fixed relevant-evidence, missing-skill, and hard-negative cases.

Done when retrieval results are traceable to source text and the fixed cases
have an inspectable assessment. Report Recall@K for labeled answerable cases;
inspect no-evidence cases separately. Choose the first method at slice start.
Hybrid comparison and reranking are not required.

### Week 6 — Evidence-backed suggestions · planned

- [ ] Assemble bounded context from requirements and confirmed evidence.
- [ ] Generate structured Japanese suggestions with references per factual claim.
- [ ] Validate references and confirmation state before displaying supported content.
- [ ] Display evidence gaps separately without inventing experience.
- [ ] Connect generation and source inspection to the HTML UI.

Done when the UI shows both a supported suggestion with inspectable sources and
an unsupported requirement with an explicit gap. Valid references alone do not
prove semantic support; assess that in evaluation.

### Week 7 — Evaluation and prompt comparison · planned

- [ ] Consolidate a small fixed synthetic dataset covering support, missing evidence,
  hard negatives, invalid references, review eligibility, and untrusted input.
- [ ] Compare a baseline prompt and one revision with inputs and model held fixed.
- [ ] Inspect semantic support and unsupported expansion manually.
- [ ] Produce a sanitized report with outputs, checks, findings, and limitations.

Done when the comparison is reproducible and case-level results are inspectable.
Reuse earlier fixed cases rather than starting a new suite. No fixed case count
or improvement percentage is required; a revision that does not improve results
is still a useful finding.

### Week 8 — Portfolio release · planned

- [ ] Resolve remaining hard-gate failures in the agreed release cases.
- [ ] Verify documented setup from a clean checkout.
- [ ] Finish README, architecture explanation, and local data-removal instructions.
- [ ] Prepare a ten-minute demo of one success and two meaningful failures.

Done when a reviewer can run the synthetic workflow and the owner can explain
retrieval, context, evidence checks, evaluation results, and limitations. This
week packages and verifies the existing workflow; it does not add features.

### Two-week progress review

Record these at each review to make pace visible:

| Period | Actual hours | Completed checkboxes / demonstrated behavior | Carried-over work and reason | Next two-week target |
| --- | --- | --- | --- | --- |
| First review after scope reset | Not yet recorded | — | — | Finish Week 4 JD workflow and Week 5 retrieval; reassess Weeks 6–8 |

At the end of each week, record what actually shipped. Move unfinished items
explicitly into the next plan and update downstream targets; preserve the
original weekly result so delays remain visible. Deferred work is not completed work.
If the five-hour cap is insufficient, revise scope or the expected finish date;
do not silently increase the weekly workload.

## 20. Deferred scope and non-goals

After the first release, reconsider these only against a concrete need:

- vector/full-text/hybrid comparison, reranking, and tokenizer experiments
- LangGraph Evidence Agent and tool-call timelines
- automated semantic judges and judge-calibration infrastructure
- frontend framework migration and visual polish
- generic RunStep/RunEvent infrastructure and detailed token/cost dashboards
- old-schema migration practice using synthetic data
- multi-source FactEvidence modeling beyond the evidence references needed by v1
- PDF/DOCX support and advanced document metadata

LangChain is not a delivery target. Multi-user access, public hosting, automatic
job applications, training, and a second large personal project are outside this
release. Deferral is not completion; adding work must replace existing scope or
wait until after release.

## 21. Demo narrative

1. Import a synthetic resume and review extracted facts.
2. Paste a JD and inspect its requirements.
3. Retrieve confirmed evidence and generate a supported suggestion.
4. Show a missing-evidence case and a rejected unsafe output.
5. Explain the fixed-case evaluation, a prompt comparison, and limitations.

## 22. Learning and collaboration protocol

Jack writes all backend code, including CRUD, persistence, API routes, model
integration, extraction validation, retrieval, context assembly, and evaluation.
The assistant explains, provides isolated examples when requested, and reviews
his work. Backend implementation is supplied only on an explicit request.

The assistant may implement UI and frontend work. Keep this distinguishable
from owner-written backend practice. Use one focused behavior and a finite test
checklist per slice; test critical behavior before implementation. Reduce repeated
explanations as familiarity grows while keeping backend coding with Jack.
Mocked tests verify software behavior; fixed real-model cases assess quality.

At each two-week review, record the delivered behavior and next small slice.
Keep the five-hour weekly cap; adjust scope rather than adding evening workload.

## 23. Deferred decisions

Choose the first retrieval method, K, evidence-reference representation, and Job
Run input representation when their slices begin. Prefer existing models and
storage until the behavior requires a change. Do not build a generic platform
for hypothetical later consumers.

## 24. Specification approval

The reduced first-release scope and collaboration protocol were approved by
Jack on 2026-09-21. The revised plan preserves the first three elapsed weeks
and schedules the remaining scope in Weeks 4–8. It supersedes the earlier
ten-week release requirements. The Week 3 ADR remains authoritative for Fact review
semantics. Deferred designs require a separate decision before implementation;
this scope approval does not approve every historical target-model field.
