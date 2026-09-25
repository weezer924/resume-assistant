# Future direction: Enterprise Private-Document Support Agent

Status: Future planning document. It does not expand the current eight-week
Resume Assistant release.

## 1. Direction

The evidence-backed Resume Assistant can later become a support Agent for
enterprise private documents. The domain changes from resume tailoring to
answering user questions from internal company knowledge. The engineering
pattern remains the same: retrieve trusted source material, generate a bounded
answer, cite the source, and show when evidence is insufficient.

## 2. Capability mapping

| Resume Assistant | Enterprise support Agent |
| --- | --- |
| Document / SourceSpan | Enterprise document / document chunk |
| Fact and Evidence | Extracted document fact and source citation |
| JobRequirement | User question or support intent |
| Confirmed-fact retrieval | Permission-filtered document retrieval |
| Evidence-backed suggestion | Citation-backed support answer |
| Missing evidence | Refusal, clarification, or human handoff |
| Review UI | Document review, answer review, and feedback UI |
| Extraction Run | Ingestion, indexing, and answer-generation Run |

## 3. Reusable foundation

The following parts of the current project are intended to transfer:

- Python, FastAPI, Pydantic, and structured model output
- prompt IDs and prompt versions
- persisted source text and provenance
- exact quote and citation validation
- confirmed-only retrieval eligibility
- bounded context assembly
- deterministic checks and fixed-case evaluation
- Run records, errors, and inspectable results

The current project should first finish its local evidence-backed RAG workflow.
The future project can then replace the domain entities while keeping these
boundaries and checks.

## 4. New domain requirements

### 4.1 Private document lifecycle

Enterprise documents need ingestion, updates, deletion, version identity, and
index refresh. Source versions must remain traceable to the answer that used
them.

### 4.2 Access control

Retrieval must apply the user's document and workspace permissions before any
content enters the prompt. A semantically relevant document is never sufficient
authorization. Permission checks must be deterministic and independently tested.

### 4.3 Support answer contract

An answer should contain:

- the user's question or support intent
- a concise answer when evidence supports it
- source document and chunk references
- an explicit uncertainty or missing-evidence result when needed
- a human-handoff recommendation when the system cannot answer safely

The Agent must not invent company policy, customer-specific facts, or actions
that are absent from authorized documents.

### 4.4 Agent boundary

Normal retrieval and deterministic checks remain the reliability-critical path.
An optional Agent may perform bounded query rewriting, repeated retrieval, or
read-only enterprise lookups. It may not bypass permissions, mutate source
documents, change review state, or publish an answer without fixed checks.

LangGraph, LangChain, or another orchestration framework is a later decision;
the framework is not the product requirement.

## 5. Evaluation focus

The future evaluation set should cover:

- directly supported answers
- missing or ambiguous policy
- conflicting document versions
- semantically similar but unauthorized documents
- permission leakage
- prompt injection inside private documents
- incorrect citations
- safe refusal and human handoff
- Japanese and multilingual support terminology

Primary hard gates are citation validity, permission safety, no unsupported
claims, and no private-data leakage. Retrieval quality, answer usefulness,
latency, and cost are measured separately.

## 6. Suggested implementation sequence

1. Reuse the current evidence and citation model with a synthetic enterprise
   document dataset.
2. Add document versions and permission metadata.
3. Build one permission-filtered retrieval baseline.
4. Generate citation-backed answers and explicit evidence gaps.
5. Add fixed-case evaluation for grounding and access control.
6. Add a bounded read-only Agent only if the baseline shows a real need.

This direction is a future adaptation plan, not a commitment to complete an
additional large project during the current eight-week schedule.
