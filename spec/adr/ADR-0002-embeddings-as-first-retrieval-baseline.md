# ADR-0002: Use OpenAI embeddings stored in SQLite as the first retrieval baseline

Date: 2026-10-19
Status: Accepted

## Decision

The Week 5 [retrieval baseline](../08-milestones-acceptance-criteria.md#week-5--one-retrieval-baseline-rag--planned)
uses OpenAI `text-embedding-3-small` vectors over confirmed Fact claims and
their evidence excerpts. Vectors live in one SQLite table as a rebuildable
projection keyed by Fact ID. Ranking is cosine similarity computed in Python
over all confirmed Facts; the application returns bounded Top-K and rechecks
confirmation state in SQLite before any consumer uses a result.

The embedding model is configured next to the extraction model in
`app/dependencies.py` ([model roles](../04-ai-and-evaluation.md#122-model-roles)).
No vector database, no orchestration framework, no hybrid fusion, no reranker.

## Parameters (2026-10-20)

- K = 5. The corpus is one person's confirmed Facts; five candidates per
  requirement fit the Week 6 context budget and keep inspection manageable.
- Query text = `normalized_requirement`. It strips JD boilerplate
  (必須／歓迎 labels, 年以上) that would otherwise dominate the vector.
  `requirement_text` is kept as a later comparison, not a second method.
- Index timing: upsert the vector when a Fact is confirmed; delete it on
  edit or reject. Read-side state recheck remains the correctness guarantee;
  the write-side hooks only keep the projection small and current.

## Context

Section 10.3 left the first method open until the slice started. Two facts
decided it:

- Fixed cases include Japanese requirements and excerpts
  ([10.4](../04-ai-and-evaluation.md#104-japanese-retrieval)). SQLite FTS5
  has no Japanese tokenizer by default, so a full-text baseline would need
  tokenizer work before it could be assessed. Embeddings sidestep that.
- The corpus is one person's confirmed Facts: hundreds of rows at most.
  In-process cosine over a SQLite table is sufficient and keeps the index a
  plain projection that can be rebuilt from the source of truth.

## Rejected

- Rejected: SQLite FTS5 full-text search first. Japanese tokenization blocks
  the fixed cases; revisit only as a post-release comparison.
- Rejected: a vector database (Chroma, sqlite-vec, pgvector). Adds a
  dependency and a second store for a corpus that fits in memory.
- Rejected: LangChain retrievers or LlamaIndex. Hides the query build,
  Top-K selection, and state recheck that the evaluation must inspect.
- Rejected: hybrid fusion or reranking in the baseline. Section 10.3 already
  defers them; they need a measured baseline to compare against.

## Consequences

- `RetrievalCandidate` ([6.7](../02-data-model.md#67-retrievalcandidate))
  records `method = "embedding:text-embedding-3-small"`, cosine score, rank,
  and selection, so a later method can be compared row for row.
- The embedding table is updated per Fact: written on confirm, removed on
  edit or reject. Stale vectors for non-confirmed Facts are ignored at read
  time, not trusted.
- Fixed cases need labeled relevant Facts and at least one semantically
  similar non-supporting Fact per requirement, so Recall@K and hard-negative
  behavior can be reported separately ([10.5](../04-ai-and-evaluation.md#105-retrieval-evaluation)).
- Embedding calls are recorded as Runs like extraction calls; failures surface
  as explicit errors, not empty results.
