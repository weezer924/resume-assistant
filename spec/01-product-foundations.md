## 1. Purpose

This project is a local-first AI application that helps one user tailor existing resume content to a specific job description without inventing skills, responsibilities, dates, or achievements.

The application must extract career facts from user-provided documents, preserve their provenance, require human confirmation, retrieve only relevant confirmed evidence, and produce Japanese resume-edit suggestions whose factual claims are traceable to evidence.

The project is also a portfolio artifact for AI Application Engineer and Forward Deployed Engineer roles. It must demonstrate a coherent production-oriented AI application rather than a collection of unrelated AI technologies.

### 1.1 Product thesis

The central product promise is:

> Every factual resume claim is supported by confirmed evidence, and missing evidence is made visible instead of being replaced by plausible fabrication.

### 1.2 Portfolio thesis

The project should provide reviewable evidence of the following capabilities:

- OpenAI Responses API integration
- domain-specific prompt design and prompt versioning
- context assembly and evidence budgeting
- structured outputs and schema validation
- RAG and hybrid retrieval
- bounded tool-calling agent workflow built with LangGraph
- deterministic safety checks
- LLM-as-judge evaluation
- human calibration of judges
- latency, token, cost, and failure observability
- privacy-aware local application design

It must not claim experience that the implementation does not demonstrate, including multi-agent systems, MCP, A2A, OCR/VLM, fine-tuning, or model training.

## 2. Goals and success criteria

### 2.1 Product goals

1. Import career evidence from supported local document formats.
2. Extract structured candidate facts while preserving exact source spans.
3. Require the user to confirm, edit, or reject extracted facts.
4. Parse a target job description into structured requirements.
5. Retrieve confirmed evidence relevant to each job requirement.
6. Generate Japanese, evidence-backed, per-item resume-edit suggestions.
7. Separate supported resume content from clarification questions and future skill-development advice.
8. Make retrieval, generation, validation, and agent behavior inspectable in a local UI.
9. Evaluate quality repeatedly across prompt and model versions.
10. Publish the code, architecture, synthetic dataset, and sanitized evaluation report without publishing personal data.

### 2.2 Portfolio-ready success

The application is portfolio-ready when all of the following are true:

- A reviewer can clone the public repository and run the application locally from documented steps.
- A synthetic resume and job description complete the primary workflow end to end.
- Every factual claim in the generated result references one or more valid Evidence IDs.
- An unsupported job requirement produces no fabricated resume experience.
- The user can inspect the source excerpt behind each generated claim.
- The public evaluation suite contains 40–60 representative cases.
- A private suite contains 10–20 real-use cases without being committed to Git.
- At least 15 outputs have human labels for judge calibration.
- A versioned evaluation report compares at least two prompt or model configurations.
- The Run Detail page explains retrieval, model calls, checks, failures, tokens, latency, and estimated cost.
- The README and demo can explain one successful case and at least two meaningful failure cases.

## 3. Target users and usage boundary

### 3.1 Primary user

The primary user is the repository owner, using personal career documents to tailor resume content for Japanese AI Application Engineer, AI Product Engineer, and FDE-adjacent roles.

### 3.2 Secondary viewers

The application may be shown locally to a small number of reviewers. Reviewers do not receive accounts and do not upload personal data. Demonstrations should use synthetic or sanitized fixtures unless the owner deliberately chooses otherwise.

### 3.3 Deployment boundary

- Source code: public GitHub repository.
- Application runtime: local only for v1.
- Personal documents and private evals: local and gitignored.
- Public demo data: synthetic and reviewable.
- Public API endpoint: none.
- Multi-user access: none.

## 4. Core user workflows

### 4.1 Import and fact confirmation

1. The user imports a supported career document.
2. The application parses the document locally into stable source spans.
3. The extraction model proposes structured candidate facts.
4. The UI displays each candidate fact with its exact source excerpt.
5. The user confirms, edits, rejects, or leaves the fact pending.
6. Only confirmed facts become eligible for retrieval and generation.
7. The retrieval projection is refreshed from the confirmed facts.

1. 用户导入一份受支持的职业相关文档。
2. 应用程序在本地解析该文档，将其转化为稳定的源文本片段。
3. 提取模型生成结构化的候选事实。
4. 用户界面展示每项候选事实及其对应的确切源文本摘录。
5. 用户对该事实进行确认、编辑、拒绝或将其标记为待处理。
6. 只有经确认的事实才会被纳入检索与生成流程。
7. 检索投影基于已确认的事实进行更新。

### 4.2 Job analysis

1. The user pastes a target job description.
2. The application treats the job description as untrusted data.
3. The extraction model returns structured job requirements.
4. The user can inspect the extracted requirements before generation.
5. Each requirement receives a stable Requirement ID.

### 4.3 Generate resume-edit suggestions

1. The fixed pipeline retrieves confirmed facts for each job requirement.
2. Candidates are ranked using hybrid retrieval and optional reranking.
3. The context builder selects a bounded evidence set.
4. The generation model creates per-item Japanese resume-edit suggestions.
5. Each factual claim must cite Evidence IDs in structured output.
6. Deterministic checks validate references, formatting, privacy, and forbidden content.
7. An LLM judge evaluates groundedness, relevance, exaggeration risk, and Japanese quality.
8. The publishing gate assigns a final result status.
9. The UI separates supported content, clarification requests, and skill-development suggestions.

### 4.4 Investigate an evidence gap

1. Fixed hybrid retrieval runs first.
2. If evidence coverage is insufficient, the UI shows the missing requirement.
3. The user may click **Investigate further**.
4. A bounded, read-only Evidence Agent searches and inspects confirmed evidence.
5. The Agent returns one structured status:
   - `SUPPORTED`
   - `PARTIALLY_SUPPORTED`
   - `NO_EVIDENCE`
   - `CONFLICTING_EVIDENCE`
6. The Agent must cite Evidence IDs or explicitly report that none were found.
7. The fixed pipeline, not the Agent, decides whether content is publishable.

### 4.5 Review and edit suggestions

For each suggestion, the UI presents:

- original resume content, when available
- proposed Japanese content
- related job requirements
- supporting evidence and source excerpt
- groundedness and safety results
- `accept`, `edit`, and `reject` actions

If the user edits a suggestion, the application stores the original generation, edited result, and optional edit reason. User edits do not automatically modify prompts or become training data.

## 5. Output contract

The final product output has three strictly separated sections.

### 5.1 Supported resume content

Content that may be copied into a resume because every factual claim has confirmed supporting evidence and passes all hard gates.

### 5.2 Evidence clarification

Questions that help the user locate or add existing real evidence. These questions must not assume that the missing experience exists.

Example intent:

> The job asks for Kubernetes production experience. No confirmed evidence was found. Do you have a project note or work record that demonstrates this experience?

### 5.3 Skill-development suggestions

Future learning or project suggestions derived from gaps between the job requirements and confirmed evidence.

These suggestions must:

- be visibly separate from resume content
- use future-oriented wording
- never be included in a generated claim
- never change a Fact to `confirmed`

