## 14. UI specification

Use the existing plain HTML, CSS, and JavaScript frontend served by FastAPI.
Provide the controls needed to observe the backend workflow and its evidence.

### 14.1 Documents

Import Markdown, show source sections, and report input errors.

### 14.2 Facts

Show pending, confirmed, and rejected Facts with original evidence. Support
confirm/edit/reject on stable IDs and show the resulting state.

### 14.3 Job

Accept pasted JD text and display extracted requirements and their
required/preferred/unspecified classification.

### 14.4 Suggestions

Display generated suggestions, related requirements, and cited source excerpts.
Show evidence gaps separately from supported content. Suggestion review history
and development-advice features are optional later work.

### 14.5 Run Detail

Expose model and prompt versions, status, results, errors, retrieval candidates,
and selected evidence through a simple inspectable view. A dedicated timeline,
generic events, and detailed cost dashboards are deferred.

### 14.6 Evals

A readable, sanitized report is sufficient. No evaluation dashboard is required.

### 14.7 Frontend testing scope

Use API integration tests for backend behavior and synthetic browser checks for
connected flows. Verify import → fact review → JD → suggestion → source inspection,
and a missing-evidence result. Add framework-specific tests only with a future
framework migration.

## 15. Supported input formats

Markdown career documents and pasted job descriptions. Empty or invalid input
produces a visible error. PDF/DOCX and URL fetching are outside the first release.

## 16. Privacy, security, and public repository boundary

### 16.1 Local data handling

Personal documents, databases, and model outputs stay local and gitignored.
Public demonstrations and fixtures use synthetic data. Document local data
storage and removal in the runbook; a deletion UI is a later convenience.

### 16.2 OpenAI API boundary

Parse locally and send only the text needed for a model call. Use `store=False`
for Responses requests without describing it as absolute zero retention.

### 16.3 Logging

General logs contain identifiers, timings, status, and safe error metadata,
not resume text, contact details, credentials, or hidden model reasoning.

### 16.4 Untrusted content

Documents and job descriptions are data, not instructions. They cannot change
confirmation state, bypass checks, reveal private context, or authorize publication.

### 16.5 Public repository content

Publish code, synthetic fixtures, specifications, sanitized reports, and setup
instructions. Exclude personal records, private outputs, API keys, and company
proprietary data or code.
