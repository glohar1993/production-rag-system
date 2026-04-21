# Production RAG System

A production-grade Retrieval-Augmented Generation (RAG) pipeline with hybrid retrieval, self-correcting document grading (CRAG), semantic caching, conversation memory, and a streaming API — built on FastAPI, Qdrant, Redis, and GPT-4o.

---

## What Problem This Solves

Plain LLMs hallucinate and have stale knowledge cutoffs. Basic RAG fixes grounding but introduces new problems: poor retrieval quality, no quality verification, expensive repeated queries, and no conversation context.

This system solves all of those:

| Problem | Solution |
|---|---|
| LLM hallucination | Ground every answer in retrieved document chunks |
| Bad retrieval quality | Hybrid dense+sparse retrieval fused via RRF |
| No relevance check | CRAG grader scores each chunk before generation |
| Expensive repeated queries | Semantic cache (Redis, cosine similarity ≥ 0.92) |
| No conversation context | Sliding-window memory with LLM query rewriting |
| PII leakage | Input + output guards redact SSN, cards, emails, phones |
| Prompt injection | Pattern-based detection on every incoming query |

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI  (routes/query.py)                                     │
│  POST /api/query          →  JSON response                      │
│  POST /api/query/stream   →  SSE token stream                   │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
     ┌─────────────────┐
     │  1. Input Guard │  max length · PII scrub · injection detect
     └────────┬────────┘
              │
              ▼
     ┌─────────────────────┐
     │  2. Conv. Memory    │  Redis: rewrite follow-ups into standalone
     └────────┬────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  3. Semantic Cache  │  Redis: cosine sim ≥ 0.92 → return instantly
     └────────┬────────────┘
              │  (cache miss)
              ▼
     ┌─────────────────────┐
     │  4. Query Router    │  LLM: factual / analytical / code /
     └────────┬────────────┘        conversational / multi_hop
              │
              ▼
     ┌──────────────────────────────────────────┐
     │  5. Hybrid Retriever                     │
     │   Dense  → BGE-base embeddings → Qdrant  │
     │   Sparse → BM25Okapi (NLTK tokenized)    │
     │   Fusion → Reciprocal Rank Fusion (RRF)  │
     └────────┬─────────────────────────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  6. Reranker        │  CrossEncoder ms-marco-MiniLM-L-6-v2
     └────────┬────────────┘
              │
              ▼
     ┌─────────────────────────────────────────────┐
     │  7. CRAG Grader                             │
     │   LLM scores each chunk 0.0–1.0             │
     │   ≥2 relevant → CORRECT  (proceed)          │
     │   =1 relevant → AMBIGUOUS (decompose+retry) │
     │   =0 relevant → INCORRECT (refuse)          │
     └────────┬────────────────────────────────────┘
              │
     ┌────────▼──────────────────────────────────────┐
     │  AMBIGUOUS path: CRAG Agent                   │
     │   LLM decomposes query into sub-queries       │
     │   Re-retrieves + reranks each sub-query       │
     │   Falls back to DuckDuckGo web search         │
     │   Merges + deduplicates results               │
     └────────┬──────────────────────────────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  8. LLM Generation  │  GPT-4o, streamed via SSE
     └────────┬────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  9. Output Guard    │  PII redaction on generated text
     └────────┬────────────┘
              │
              ▼
     ┌──────────────────────────┐
     │  10. Cache + Memory Write│  store answer; persist turn
     └──────────────────────────┘
              │
              ▼
    Response: answer + citations + CRAG grade + query type + latency
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI 0.111 + uvicorn | Async HTTP, SSE streaming, OpenAPI docs |
| LLM | GPT-4o (OpenAI) | Generation, routing, grading, query rewriting |
| Vector DB | Qdrant | Dense vector storage + HNSW ANN search |
| Dense embeddings | BAAI/bge-base-en-v1.5 (768-dim) | Semantic retrieval |
| Sparse search | BM25Okapi (rank-bm25) | Keyword / exact-match retrieval |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 | Precision rescoring |
| Cache + Memory | Redis | Semantic cache + conversation history |
| Observability | OPIK | End-to-end pipeline tracing |
| Security | Custom guards | PII scrubbing, injection detection |
| Containerization | Docker (multi-stage) | Non-root, slim image |

---

## Project Layout

```
production-rag-system/
├── app/
│   ├── config.py          # All settings via env vars (pydantic-settings)
│   ├── main.py            # FastAPI app factory, lifespan, middleware
│   ├── models.py          # Shared Pydantic schemas
│   └── Dockerfile         # Multi-stage Docker image
├── routes/
│   ├── query.py           # POST /api/query  +  POST /api/query/stream
│   ├── search.py          # POST /api/search (debug — raw retrieval)
│   └── health.py          # GET  /health     +  GET /health/live
├── services/
│   ├── rag_pipeline.py    # Main orchestrator — all 10 stages
│   ├── semantic_cache.py  # Redis vector cache (cosine similarity)
│   ├── conversation.py    # Sliding-window session memory
│   ├── query_router.py    # LLM-based query classifier
│   ├── document_grader.py # CRAG relevance grader (per chunk)
│   └── query_decomposer.py# Breaks AMBIGUOUS queries into sub-queries
├── retrieval/
│   ├── hybrid_retriever.py# Dense + Sparse + RRF fusion
│   ├── reranker.py        # Cross-encoder rescoring
│   └── filters.py         # Qdrant metadata filter builder
├── agents/
│   └── crag.py            # CRAG agent (sub-query retrieval + web fallback)
├── security/
│   ├── input_guard.py     # Query sanitization (PII, injection, length)
│   └── output_guard.py    # Answer PII redaction
├── prompts/
│   ├── templates.py       # System + user prompt builders
│   └── grading.py         # Relevance grading prompt
├── tools/
│   └── web_search.py      # DuckDuckGo Instant Answer fallback
├── static/
│   └── index.html         # Browser UI (Chat + Debug Search tabs)
├── seed_qdrant.py         # One-time script to index sample documents
├── pyproject.toml         # Dependencies + tool config
└── .env.example           # Environment variable template
```

---

## Quick Start — Local Development

### Prerequisites

- Python 3.11+
- Docker (for Qdrant + Redis)
- OpenAI API key

### 1. Start infrastructure

```bash
# Qdrant vector database
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY
```

### 4. Seed the vector store

```bash
python seed_qdrant.py
# Output: Indexed 8 documents into 'rag_documents'
```

### 5. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** for the browser UI or **http://localhost:8000/docs** for the interactive API explorer.

---

## Environment Variables

All settings are in `app/config.py`. Copy `.env.example` to `.env`.

| Variable | Default | Required | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | — | **Yes** | OpenAI API key (GPT-4o) |
| `QDRANT_URL` | `http://localhost:6333` | No | Qdrant server URL |
| `QDRANT_API_KEY` | — | No | Qdrant Cloud API key |
| `QDRANT_COLLECTION` | `rag_documents` | No | Collection name |
| `REDIS_URL` | `redis://localhost:6379/0` | No | Redis connection URL |
| `LLM_MODEL` | `gpt-4o` | No | OpenAI model name |
| `LLM_MAX_TOKENS` | `4096` | No | Max generation tokens |
| `DENSE_EMBED_MODEL` | `BAAI/bge-base-en-v1.5` | No | HuggingFace embedding model |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | No | CrossEncoder model |
| `SEMANTIC_CACHE_THRESHOLD` | `0.92` | No | Cosine similarity threshold for cache hit |
| `SEMANTIC_CACHE_TTL` | `3600` | No | Cache TTL in seconds |
| `CRAG_RELEVANCE_THRESHOLD` | `0.6` | No | Min chunk relevance score (0–1) |
| `PII_REDACTION` | `true` | No | Enable PII scrubbing on input + output |
| `OPIK_API_KEY` | — | No | OPIK observability key |
| `ENV` | `development` | No | `development` enables /docs; `production` disables it |

---

## API Reference

### `POST /api/query`

Full pipeline, returns JSON when generation is complete.

**Request**
```json
{
  "query": "What is hybrid retrieval?",
  "session_id": "user-123",
  "top_k": 5,
  "filters": { "doc_type": "technical" },
  "stream": false
}
```

**Response**
```json
{
  "answer": "Hybrid retrieval fuses dense and sparse search...",
  "citations": [
    { "text": "...", "source": "hybrid_retrieval.md", "chunk_id": "abc", "score": 8.2 }
  ],
  "query_type": "factual",
  "crag_grade": "correct",
  "cached": false,
  "trace_id": "a3f...",
  "latency_ms": 9420.5
}
```

---

### `POST /api/query/stream`

Same pipeline, streamed as Server-Sent Events (SSE).

**Events received (in order)**

| Event | Data | When |
|---|---|---|
| `token` | `"partial text..."` | One per LLM output chunk |
| `citations` | `[{...}]` JSON array | After generation completes |
| `done` | `{"cached": false, "grade": "correct", "trace_id": "..."}` | Always last |
| `error` | `"error message"` | On failure |

**JavaScript example**
```js
const res = await fetch('/api/query/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'What is RAG?', session_id: 'demo' }),
});

const reader = res.body.getReader();
const decoder = new TextDecoder();
let buf = '';

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

  for (const block of buf.split('\n\n')) {
    let type = '', data = [];
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) type = line.slice(7);
      else if (line.startsWith('data: ')) data.push(line.slice(6));
    }
    if (type === 'token') process.stdout.write(data.join('\n'));
  }
  buf = '';
}
```

---

### `POST /api/search`

Raw hybrid retrieval without generation — useful for debugging retrieval quality.

**Request**
```json
{ "query": "hybrid retrieval", "top_k": 5, "filters": {} }
```

**Response**
```json
{
  "chunks": [
    { "id": "abc", "content": "...", "source": "hybrid_retrieval.md", "score": 8.17, "metadata": {} }
  ],
  "latency_ms": 142.3
}
```

---

### `GET /health`

Returns status of all dependencies.

```json
{
  "status": "ok",
  "components": [
    { "name": "qdrant", "healthy": true, "latency_ms": 12.4, "detail": "" },
    { "name": "redis",  "healthy": true, "latency_ms": 1.2,  "detail": "" },
    { "name": "llm",    "healthy": true, "latency_ms": 890.0, "detail": "" }
  ]
}
```

### `GET /health/live`

Kubernetes liveness probe — returns `{"status": "alive"}` if the process is running.

---

## Running with Docker

```bash
# Build
docker build -f app/Dockerfile -t production-rag:latest .

# Run (assumes Qdrant and Redis are accessible)
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e QDRANT_URL=http://host.docker.internal:6333 \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  production-rag:latest
```

---

## CRAG Grading — How It Works

CRAG (Corrective RAG) prevents hallucination by verifying retrieval quality before generation:

```
For each retrieved chunk:
    LLM score = relevance to query (0.0 – 1.0)

n_relevant = chunks where score ≥ 0.6

n_relevant ≥ 2  →  CORRECT   → generate directly
n_relevant == 1 →  AMBIGUOUS → decompose query → re-retrieve → web fallback → generate
n_relevant == 0 →  INCORRECT → refuse: "I couldn't find reliable information"
```

The CRAG grade is returned in every response so you can monitor retrieval health over time.

---

## Semantic Cache

Avoids expensive LLM calls for semantically equivalent questions:

```
"What is RAG?"  →  embedded  →  compare against cached query vectors
                               if cosine_similarity ≥ 0.92  →  return cached answer
                               else  →  run full pipeline  →  cache the new answer
```

Cached answers return in ~50ms vs ~10s for a full pipeline run. TTL defaults to 1 hour.

---

## Observability

Every pipeline run is traced via OPIK. Set `OPIK_API_KEY` in `.env` to enable. Traces include:

- Stage-by-stage latency (retrieval, grading, generation)
- CRAG grade and chunk scores
- Cache hit/miss
- Query type classification
- Token counts

---

## Security

| Threat | Mitigation |
|---|---|
| Prompt injection | Regex detection on 5 injection patterns; logged for monitoring |
| PII in queries | SSN, credit card, email redacted before hitting the LLM |
| PII in answers | Output guard redacts SSN, card, email, phone from generated text |
| Oversized queries | Hard limit: 2000 characters |
| Non-root container | Docker image runs as `appuser` (no root privileges) |

---

## Development

```bash
# Lint
ruff check .

# Type check
mypy .

# Tests
pytest tests/ -v
```

---

## Sample Queries for Testing

The seeded index contains 8 technical documents. These queries work well:

| Query | Expected CRAG | Notes |
|---|---|---|
| `What is RAG and how does it work?` | correct | Core concept in index |
| `Explain hybrid retrieval with RRF fusion` | ambiguous | Triggers CRAG agent |
| `How does semantic caching reduce latency?` | correct | Hits semantic_cache.md |
| `How does cross-encoder reranking work?` | ambiguous | Some relevant chunks |
| `What vector types does Qdrant support?` | correct | Hits qdrant_docs.md |
| `What is the meaning of life?` | incorrect | Not in index → refuses |

Send the same question twice to observe ⚡ cached on the second request.
