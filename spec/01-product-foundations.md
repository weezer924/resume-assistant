## 1. Purpose

This project is a local-first AI application that helps one user tailor existing resume content to a specific job description without inventing skills, responsibilities, dates, or achievements.

The application must extract career facts from user-provided documents, preserve their provenance, require human confirmation, retrieve only relevant confirmed evidence, and produce Japanese resume-edit suggestions whose factual claims are traceable to evidence.

The project is also a portfolio artifact for AI Application Engineer and Forward Deployed Engineer roles. It must demonstrate a coherent production-oriented AI application rather than a collection of unrelated AI technologies.

### 1.1 Product thesis

The central product promise is:

> Every factual resume claim is supported by confirmed evidence, and missing evidence is made visible instead of being replaced by plausible fabrication.

### 1.2 Portfolio thesis

The project demonstrates owner-written Python model integration, structured
extraction, provenance, RAG, bounded context assembly, deterministic validation,
and fixed-case evaluation. Public claims must match implemented evidence.

## 2. Goals and success criteria

### 2.1 Product goals

1. Import Markdown career documents and preserve source spans.
2. Extract facts for human confirmation, editing, or rejection.
3. Parse pasted job descriptions into inspectable requirements.
4. Retrieve relevant confirmed evidence using one baseline method.
5. Generate Japanese suggestions with traceable factual claims.
6. Make missing evidence visible and keep it separate from resume content.
7. Evaluate fixed cases and publish a sanitized comparison report.

### 2.2 Portfolio-ready success

- A clean checkout can run the documented local workflow with synthetic data.
- A reviewer can follow import, review, job analysis, retrieval, and generation.
- Factual claims reference confirmed evidence that resolves to saved source text.
- Missing evidence produces an explicit gap rather than fabricated experience.
- A fixed-case report compares a baseline prompt and one revision, showing
  outputs, checks, human assessment, and limitations.
- A ten-minute demo explains one success, two failures, and key trade-offs.

Release stages and acceptance are defined in
[milestones](08-milestones-acceptance-criteria.md).

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

### 4.2 Job analysis

1. The user pastes a target job description.
2. The application treats the job description as untrusted data.
3. The extraction model returns structured job requirements.
4. The user can inspect the extracted requirements before generation.
5. Each requirement receives a stable Requirement ID.

### 4.3 Generate resume-edit suggestions

1. The fixed pipeline retrieves confirmed facts for each job requirement.
2. Candidates are ranked by the selected baseline retrieval method.
3. The context builder selects a bounded evidence set.
4. The generation model creates per-item Japanese resume-edit suggestions.
5. Each factual claim must cite Evidence IDs in structured output.
6. Deterministic checks validate references, formatting, privacy, and forbidden content.
7. Semantic support and writing quality are assessed in the fixed-case evaluation.
8. The publishing gate assigns a final result status.
9. The UI separates supported content from evidence gaps.

### 4.4 Inspect results

The user inspects proposed content, related requirements, and supporting source
excerpts. The interface separates supported content from evidence gaps.
Suggestion editing workflows and deeper Agent investigation are post-release
extensions.

## 5. Output contract

The first release separates supported content from evidence clarification.
Optional development advice must remain separate from both.

### 5.1 Supported resume content

Content that may be copied into a resume because every factual claim has confirmed supporting evidence and passes all hard gates.

### 5.2 Evidence clarification

Questions that help the user locate or add existing real evidence. These questions must not assume that the missing experience exists.

Example intent:

> The job asks for Kubernetes production experience. No confirmed evidence was found. Do you have a project note or work record that demonstrates this experience?

### 5.3 Skill-development suggestions (optional extension)

Future learning or project suggestions derived from gaps between the job requirements and confirmed evidence.

These suggestions must:

- be visibly separate from resume content
- use future-oriented wording
- never be included in a generated claim
- never change a Fact to `confirmed`

