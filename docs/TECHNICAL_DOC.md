# Production RAG System — Complete Technical Document

> Written for engineers who want to understand every file, every flow, and every design decision in this system from scratch.

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [The Problem It Solves](#2-the-problem-it-solves)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Directory Structure](#4-directory-structure)
5. [Infrastructure Components](#5-infrastructure-components)
6. [Every File Explained](#6-every-file-explained)
   - [app/](#61-app-layer)
   - [routes/](#62-routes-layer)
   - [services/](#63-services-layer)
   - [retrieval/](#64-retrieval-layer)
   - [agents/](#65-agents-layer)
   - [security/](#66-security-layer)
   - [prompts/](#67-prompts-layer)
   - [tools/](#68-tools-layer)
   - [seed_qdrant.py](#69-seed_qdrantpy)
   - [static/index.html](#610-staticindexhtml)
7. [Complete Request Flow — Step by Step](#7-complete-request-flow--step-by-step)
8. [CRAG Decision Tree](#8-crag-decision-tree)
9. [Data Models Reference](#9-data-models-reference)
10. [Configuration Reference](#10-configuration-reference)
11. [API Reference](#11-api-reference)
12. [How Embeddings Work](#12-how-embeddings-work)
13. [How Scoring Works](#13-how-scoring-works)
14. [Knowledge Base — What Data Is Indexed](#14-knowledge-base--what-data-is-indexed)
15. [How to Add Your Own Data](#15-how-to-add-your-own-data)
16. [Running the System Locally](#16-running-the-system-locally)

---

## 1. What This System Does

This is a **production-grade Question Answering system** built on the RAG (Retrieval-Augmented Generation) pattern. You give it a question in plain English. It searches a knowledge base, evaluates the quality of what it found, and generates a precise answer grounded in real retrieved documents.

It is NOT a chatbot that guesses from training data. It answers from **your documents**.

If your documents don't have the answer, it falls back to **live web search** (DuckDuckGo, no API key needed). If neither has the answer, it refuses rather than making something up.

---

## 2. The Problem It Solves

Standard LLMs (like GPT-4) have two problems:

| Problem | How this system fixes it |
|---------|--------------------------|
| **Hallucination** — model invents facts | Answers are generated ONLY from retrieved chunks. If context is empty, the model says so. |
| **Stale knowledge** — model training cutoff | Live web search fallback provides real-time information. |
| **No citations** — you can't verify the answer | Every response includes citations with source, score, and content excerpt. |
| **Slow repeated queries** — every query hits the LLM | Semantic cache returns cached answers for similar questions in milliseconds. |
| **Follow-up questions lose context** | Conversation memory rewrites follow-up queries into standalone ones before retrieval. |

---

## 3. High-Level Architecture

```
User Query
    │
    ▼
┌─────────────┐
│ Input Guard │  ← Sanitize PII, strip injection patterns, enforce length
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Conversation     │  ← Rewrite follow-up query into standalone (using Redis history)
│ Memory (Redis)   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Semantic Cache   │  ← If similar query seen before (cosine ≥ 0.92), return cached answer
│ (Redis)          │    (skips everything below)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Query Router     │  ← Classify: factual / analytical / conversational / code / multi_hop
│ (GPT-4o)         │    Adjusts how many documents to fetch
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Hybrid Retriever                     │
│  ├─ Dense: BGE embeddings → Qdrant   │  ← Semantic meaning search
│  └─ Sparse: BM25 keyword search      │  ← Exact keyword search
│       └─ Fused via RRF               │  ← Best of both worlds
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Cross-Encoder    │  ← Rescore all retrieved chunks for precise query-document relevance
│ Reranker         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ CRAG Grader      │  ← Ask GPT-4o: is each chunk relevant? (score 0.0–1.0)
│ (GPT-4o)         │    Decide: CORRECT / AMBIGUOUS / INCORRECT
└──────┬───────────┘
       │
   ┌───┴──────────────────┐
   │                      │
INCORRECT              AMBIGUOUS
   │                      │
   ▼                      ▼
Web Search         Query Decomposer (GPT-4o)
(DuckDuckGo)       breaks into 2-4 sub-queries
   │               → re-retrieves from Qdrant
   │               → merges + deduplicates
   │                      │
   └──────────┬───────────┘
              │
              ▼
      ┌──────────────┐
      │ GPT-4o       │  ← Generate answer from retrieved chunks + conversation history
      │ Generation   │    System prompt varies by query type
      └──────┬───────┘
             │
             ▼
      ┌──────────────┐
      │ Output Guard │  ← Redact PII from generated answer
      └──────┬───────┘
             │
             ▼
      ┌──────────────────────┐
      │ Cache + Memory Store │  ← Save answer to semantic cache + update conversation
      └──────┬───────────────┘
             │
             ▼
      Response with answer + citations + grade + latency
```

---

## 4. Directory Structure

```
production-rag-system/
│
├── app/                        # FastAPI core
│   ├── main.py                 # App factory, lifespan, middleware, routes
│   ├── config.py               # All settings via environment variables
│   └── models.py               # Pydantic schemas (request/response shapes)
│
├── routes/                     # HTTP endpoint handlers
│   ├── query.py                # POST /api/query and /api/query/stream
│   ├── search.py               # POST /api/search (debug: raw retrieval only)
│   └── health.py               # GET /health (checks Qdrant + Redis + LLM)
│
├── services/                   # Core business logic
│   ├── rag_pipeline.py         # Master orchestrator — calls everything in order
│   ├── semantic_cache.py       # Redis-backed semantic similarity cache
│   ├── conversation.py         # Sliding window conversation memory in Redis
│   ├── query_router.py         # Classify query type via GPT-4o
│   ├── document_grader.py      # CRAG: grade each chunk's relevance via GPT-4o
│   └── query_decomposer.py     # CRAG: break complex queries into sub-queries
│
├── retrieval/                  # Document search layer
│   ├── hybrid_retriever.py     # Dense (Qdrant BGE) + Sparse (BM25) fused via RRF
│   ├── reranker.py             # Cross-encoder reranker (ms-marco-MiniLM)
│   └── filters.py              # Post-retrieval score/metadata/near-dedup filters
│
├── agents/                     # Autonomous agents
│   └── crag.py                 # CRAG agent: sub-query retrieval + merge
│
├── security/                   # Input/output protection
│   ├── input_guard.py          # Sanitize queries: length, injection, PII
│   └── output_guard.py         # Redact PII from generated answers
│
├── prompts/                    # All LLM prompt strings
│   ├── templates.py            # RAG generation prompt + query routing prompt
│   └── grading.py              # CRAG document relevance grading prompt
│
├── tools/                      # External integrations
│   └── web_search.py           # DuckDuckGo web search (no API key)
│
├── static/
│   └── index.html              # Frontend UI (full-page chat + debug search)
│
├── seed_qdrant.py              # One-time script to initialize Qdrant with sample data
├── pyproject.toml              # Python dependencies and project metadata
├── .env                        # Secret environment variables (never commit)
└── .env.example                # Template showing what env vars are needed
```

---

## 5. Infrastructure Components

The system requires three external services running locally:

### Qdrant (Vector Database)
- **What it is**: A vector search engine. Stores document embeddings (768-dimensional float arrays) and retrieves the most similar ones for any query embedding.
- **Port**: `6333`
- **How to start**: `docker run -p 6333:6333 qdrant/qdrant`
- **What's stored**: Each document chunk = `{ id, vector[768], payload: { content, source, doc_type, language } }`
- **Search method**: HNSW (Hierarchical Navigable Small World graph) — approximate nearest neighbor, very fast even at millions of vectors.

### Redis (Cache + Memory)
- **What it is**: An in-memory key-value store. Used for two purposes: semantic cache and conversation memory.
- **Port**: `6379`
- **How to start**: `docker run -p 6379:6379 redis`
- **Semantic cache keys**:
  - `semcache:vectors` — list of binary-encoded embedding vectors
  - `semcache:meta` — list of JSON strings `{"query": "...", "answer": "..."}`
- **Conversation memory keys**:
  - `conv:{session_id}` — JSON array of `{"role": "user"/"assistant", "content": "..."}` turns

### OpenAI API (GPT-4o)
- **What it is**: The language model used for query classification, document grading, query rewriting, query decomposition, and answer generation.
- **Model**: `gpt-4o` (configurable)
- **Used in**: `query_router.py`, `document_grader.py`, `conversation.py`, `query_decomposer.py`, `rag_pipeline.py`
- **Required**: `OPENAI_API_KEY` in `.env`

---

## 6. Every File Explained

### 6.1 App Layer

#### `app/config.py`
The single source of truth for all configuration. Uses `pydantic-settings` which automatically reads values from environment variables and the `.env` file.

Key settings and what they control:

| Setting | Default | What it does |
|---------|---------|--------------|
| `openai_api_key` | `""` | Required. Used by all GPT-4o calls. |
| `llm_model` | `gpt-4o` | Which OpenAI model to use for generation. |
| `llm_max_tokens` | `4096` | Max tokens in the generated answer. |
| `llm_temperature` | `0.0` | 0 = fully deterministic. Higher = more creative. |
| `dense_embed_model` | `BAAI/bge-base-en-v1.5` | Sentence transformer for turning text into 768-dim vectors. |
| `reranker_model` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder model for precise reranking. |
| `qdrant_url` | `http://localhost:6333` | Where Qdrant is running. |
| `qdrant_collection` | `rag_documents` | Name of the collection inside Qdrant. |
| `redis_url` | `redis://localhost:6379/0` | Where Redis is running. |
| `semantic_cache_ttl` | `3600` | Seconds before cached answers expire (1 hour). |
| `semantic_cache_threshold` | `0.92` | Cosine similarity score required to return a cached answer. |
| `conversation_window` | `10` | How many conversation turns to remember per session. |
| `top_k_dense` | `20` | How many results to fetch from Qdrant per query. |
| `top_k_sparse` | `20` | How many results BM25 returns. |
| `top_k_rerank` | `5` | How many chunks survive after reranking. |
| `rrf_k` | `60` | RRF fusion constant. Higher = less difference between ranks. |
| `crag_relevance_threshold` | `0.6` | Minimum GPT-4o relevance score to consider a chunk "relevant". |
| `crag_max_web_results` | `3` | Max web search results to fetch as fallback. |
| `max_query_length` | `2000` | Input guard: truncate queries longer than this. |
| `pii_redaction` | `true` | Whether to scrub SSN, credit card, email patterns. |

---

#### `app/models.py`
All Pydantic data schemas shared across the application.

**`DocumentChunk`** — the core unit of information:
```
id: str           → unique UUID assigned at indexing time
content: str      → the actual text content
metadata: dict    → extra fields: source_type, url, doc_type, language
score: float      → relevance score (reranker output or web position score)
source: str       → display label (e.g. "en.wikipedia.org", "rag_overview.md")
```

**`QueryRequest`** — what the client sends:
```
query: str        → the user's question (max 2000 chars)
session_id: str   → identifies the conversation (default: "default")
top_k: int        → how many final chunks to use for generation (1–20, default 5)
filters: dict     → optional Qdrant metadata filters (e.g. {"doc_type": "technical"})
stream: bool      → whether to use SSE streaming (default: true)
```

**`QueryResponse`** — what the server returns:
```
answer: str           → the generated text answer
citations: list       → up to 5 source chunks used
query_type: str       → factual / analytical / conversational / code / multi_hop
crag_grade: str       → correct / ambiguous / incorrect
cached: bool          → whether this was returned from semantic cache
trace_id: str         → UUID for log correlation
latency_ms: float     → total end-to-end time
```

**`CRAGGrade`** — the three possible retrieval quality grades:
- `CORRECT` — 2 or more relevant chunks found in the index
- `AMBIGUOUS` — exactly 1 relevant chunk found (query gets decomposed)
- `INCORRECT` — 0 relevant chunks found (falls back to web search)

**`QueryType`** — five query classifications:
- `FACTUAL` — direct fact lookup ("What is RAG?")
- `ANALYTICAL` — requires reasoning over multiple facts ("Compare BM25 and dense retrieval")
- `CONVERSATIONAL` — casual follow-up ("Tell me more about that")
- `CODE` — programming question ("Show me how to use Qdrant in Python")
- `MULTI_HOP` — chains multiple facts ("What model does this system use and who made it?")

---

#### `app/main.py`
The FastAPI application factory.

**Lifespan** (startup/shutdown):
- Configures Opik observability if API key is set
- Pre-warms models: loads `SemanticCache`, `HybridRetriever`, `Reranker` into memory
  - This forces the sentence-transformer models to download and load on startup instead of on first request

**Middleware**:
- CORS: allows all origins by default (tighten in production)

**Routes registered**:
- `/api` prefix → query and search routes
- No prefix → health routes
- `/` → serves `static/index.html` (the frontend)
- `/static` → serves static files

**OpenAPI docs**: available at `/docs` in development, disabled in production.

---

### 6.2 Routes Layer

#### `routes/query.py`
Two endpoints:

**`POST /api/query`** — standard JSON response:
1. Generates a `trace_id` (UUID for log correlation)
2. Passes query through `InputGuard.sanitize()`
3. Calls `pipeline.run()` — the full pipeline
4. Applies `OutputGuard.redact()` to the answer
5. Returns complete `QueryResponse`

**`POST /api/query/stream`** — Server-Sent Events (SSE):
1. Same input guard
2. Calls `pipeline.stream()` which is an async generator
3. Each iteration yields one of these SSE events:
   - `event: token` — one piece of the answer text (streamed live)
   - `event: citations` — JSON array of citations (sent after generation completes)
   - `event: done` — signals end of stream, includes grade and trace_id
   - `event: error` — if something goes wrong mid-stream

The frontend listens to the SSE stream and appends each token to the chat bubble in real time.

---

#### `routes/search.py`
**`POST /api/search`** — debug endpoint, does retrieval only, no generation:
1. Runs `HybridRetriever.retrieve()`
2. Runs `Reranker.rerank()`
3. Returns raw `DocumentChunk` list with scores

Used in the "Debug Search" tab of the frontend to inspect what the retriever actually finds for a query.

---

#### `routes/health.py`
**`GET /health`** — full readiness check:
- Pings Qdrant: calls `get_collections()` and measures latency
- Pings Redis: sends `PING` command
- Pings LLM: sends `gpt-4o` a 1-token "ping" request

Returns:
```json
{
  "status": "ok",
  "components": [
    {"name": "qdrant", "healthy": true, "latency_ms": 12.3},
    {"name": "redis",  "healthy": true, "latency_ms": 0.8},
    {"name": "llm",    "healthy": true, "latency_ms": 450.0}
  ]
}
```

**`GET /health/live`** — Kubernetes liveness probe. Just returns `{"status": "alive"}`. Does not check dependencies — only confirms the Python process is running.

---

### 6.3 Services Layer

#### `services/rag_pipeline.py`
The master orchestrator. This is the most important file in the system. It calls every other component in the correct order.

**Constructor** — instantiates all components:
```python
self._llm        = openai.AsyncOpenAI(...)    # GPT-4o client
self._cache      = SemanticCache()            # Redis semantic cache
self._memory     = ConversationMemory()       # Redis conversation history
self._router     = QueryRouter()              # Query classification
self._retriever  = HybridRetriever()          # Dense + sparse retrieval
self._reranker   = Reranker()                # Cross-encoder reranking
self._grader     = DocumentGrader()          # CRAG relevance grading
self._decomposer = QueryDecomposer()         # Sub-query generation
self._crag       = CRAGAgent()              # CRAG re-retrieval
self._web        = WebSearchTool()           # DuckDuckGo web search
self._filter     = MetadataFilter()          # Post-retrieval filtering
self._output_guard = OutputGuard()           # PII redaction
```

**`run()` method** (non-streaming, 10 steps):

| Step | What happens |
|------|--------------|
| 1 | Memory rewrites follow-up query into standalone question |
| 2 | Semantic cache checked — if hit, return immediately |
| 3 | Query classified (factual/analytical/etc.) → adjusts `top_k` |
| 4 | Hybrid retrieval: Qdrant dense + BM25 sparse → RRF fusion |
| 5 | Cross-encoder reranker rescores chunks |
| 6 | CRAG grader evaluates chunk relevance |
| 6a | If INCORRECT → web search fallback |
| 6b | If AMBIGUOUS → decompose + re-retrieve (elif, NOT if — prevents cascade) |
| 7 | GPT-4o generates answer from chunks + history |
| 8 | Citations extracted (top 5 chunks) |
| 9 | Output guard redacts PII from answer |
| 10 | Answer cached in Redis + conversation memory updated |

**`stream()` method** — identical flow, but steps 7–10 use `stream=True` on the OpenAI call. Each token chunk is yielded as a `StreamEvent(event="token", data=text)` the moment it arrives from OpenAI.

---

#### `services/semantic_cache.py`
Stores query→answer pairs in Redis. On each new query, computes cosine similarity against every stored query embedding. If similarity ≥ 0.92, returns the cached answer.

**How it stores data**:
- Two Redis lists (same index positions correspond):
  - `semcache:vectors` — raw bytes of `float32[768]` embedding
  - `semcache:meta` — JSON `{"query": "...", "answer": "..."}`

**Why 0.92 threshold?**: High enough to avoid false positives (different questions sounding similar) but catches rephrasing of the same question ("What is RAG?" and "Explain RAG to me" should both hit the cache).

**Limitation**: For large scale (millions of queries), replace the linear scan with Redis Stack's vector index (`FT.SEARCH` with `VECTOR` type).

---

#### `services/conversation.py`
Stores conversation history per session in Redis with a 24-hour TTL.

**Key format**: `conv:{session_id}` — JSON array of `{role, content}` dicts.

**Sliding window**: Keeps only the last `conversation_window * 2` messages (default: 20 messages = 10 turns). Older messages are truncated.

**Query rewriting**: If conversation history exists, sends the last 4 turns + the new question to GPT-4o with this prompt:
```
"Rewrite the follow-up question as a standalone question that captures all necessary context."
```

Example:
- Turn 1: "What is RAG?" → "What is RAG?"
- Turn 2: "How does it handle missing data?" → rewritten to → "How does a RAG system handle cases where the retrieved documents don't contain relevant information?"

This is critical for retrieval quality. Without rewriting, "it" in turn 2 would be passed to the embedder and retrieve nothing meaningful.

---

#### `services/query_router.py`
Asks GPT-4o to classify the query into one of 5 types. Adjusts `top_k` (how many documents to retrieve) based on query complexity:

| Query type | top_k multiplier | Reason |
|------------|-----------------|--------|
| `multi_hop` | 3× | Needs many facts from different parts of the knowledge base |
| `analytical` | 2× | Needs context from multiple perspectives |
| `code` | 2× | May need both docs and code examples |
| `factual` | 1× | One precise chunk is usually enough |
| `conversational` | 1× | Brief context is fine |

If base `top_k=5` and query is `analytical`, it retrieves `top_k=10` chunks.

---

#### `services/document_grader.py`
The core of CRAG. For each retrieved chunk, asks GPT-4o:
```
"Query: {query}
Document chunk: {chunk.content[:1000]}
Rate relevance 0.0 to 1.0 (output only the number):"
```

**Aggregation logic**:
- Count chunks with score ≥ `crag_relevance_threshold` (default 0.6)
- 2+ relevant chunks → `CORRECT`
- Exactly 1 relevant chunk → `AMBIGUOUS`
- 0 relevant chunks → `INCORRECT`

Returns both the grade AND the list of relevant-only chunks (the irrelevant ones are discarded).

---

#### `services/query_decomposer.py`
When CRAG grades `AMBIGUOUS`, this breaks the original query into 2–4 sub-questions.

Example:
- Original: "How does the semantic cache in this system work and what threshold does it use?"
- Sub-queries:
  1. "How does the semantic cache work?"
  2. "What similarity threshold does the semantic cache use?"
  3. "What database backs the semantic cache?"

Each sub-query is then retrieved independently, giving a richer, more targeted set of chunks to fill the knowledge gap.

---

### 6.4 Retrieval Layer

#### `retrieval/hybrid_retriever.py`
Two retrieval signals combined:

**Dense retrieval (Qdrant + BGE)**:
1. Encode the query with `BAAI/bge-base-en-v1.5` → 768-dimensional float vector
2. Query Qdrant using cosine similarity → returns top-20 `ScoredPoint` objects
3. Each point has an ID and payload (content, source, doc_type, language)

**Sparse retrieval (BM25)**:
- BM25 (Best Match 25) is a keyword frequency algorithm — the same one used by Elasticsearch
- On startup, loads all document texts from Qdrant and builds an in-memory BM25 index
- For a query, tokenizes it, computes BM25 scores for every document
- Returns top-20 (id, score) pairs

**Why hybrid?**
- Dense: "What are the benefits of vector databases?" matches chunks talking about "advantages of embedding stores" — same meaning, different words
- Sparse: "HNSW algorithm" finds exact mentions of "HNSW" — dense alone might miss this acronym
- Together they cover both semantic similarity AND keyword precision

**RRF Fusion (Reciprocal Rank Fusion)**:
```
RRF_score(document) = 1/(k + rank_in_dense) + 1/(k + rank_in_sparse)
```
Where `k=60` (the `rrf_k` setting). Documents ranked highly in both lists get the highest combined score. This works without normalizing the original scores from each system — only ranks matter.

---

#### `retrieval/reranker.py`
Takes the top-N fused chunks and rescores them using a **cross-encoder**.

**Why rerank?** The bi-encoder (BGE) encodes query and document separately. A cross-encoder processes query + document together, seeing both at once — far more accurate but slower (can't pre-compute).

**Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Trained on MS MARCO passage ranking dataset
- Outputs a single relevance score per (query, document) pair
- The score replaces the RRF fusion score

Input: up to 20 chunks from hybrid retrieval
Output: top-5 chunks (by default, configurable via `top_k_rerank`) with new precise scores

---

#### `retrieval/filters.py`
Post-retrieval filter utilities (not currently called in the main pipeline but available):

- `by_score(threshold)` — drop chunks below a minimum score
- `by_metadata(allowed)` — keep only chunks matching specific metadata values (e.g. `{"language": ["en"]}`)
- `deduplicate_near(overlap_threshold=0.8)` — removes near-duplicate chunks using 3-gram token overlap

---

### 6.5 Agents Layer

#### `agents/crag.py`
The CRAG Agent handles the `AMBIGUOUS` path. It takes the list of sub-queries generated by `QueryDecomposer` and retrieves context for each one in parallel.

For each sub-query:
1. Run `HybridRetriever` (top-10)
2. Run `Reranker` (top-3)
3. If the top score is still below the relevance threshold, do a web search for this specific sub-query

All results from all sub-queries are merged and deduplicated by ID.

This fills in knowledge gaps: the main query might have only 1 relevant chunk (AMBIGUOUS), but sub-query 1 finds chunk A and sub-query 2 finds chunk B, giving the generator enough to produce a complete answer.

---

### 6.6 Security Layer

#### `security/input_guard.py`
Applied to every query before it enters the pipeline.

**Step 1 — Length enforcement**: Truncates to `max_query_length` (2000 chars). Prevents token-flooding attacks.

**Step 2 — Whitespace normalization**: Strips leading/trailing whitespace.

**Step 3 — Prompt injection detection**: Scans for patterns like:
- `"ignore all previous instructions"`
- `"you are now a..."`
- `"system:"` prefix
- `<script>`, `<iframe>` HTML tags
- ` ```system ` markdown blocks

Currently logs a warning but still allows the query (for monitoring). To block: raise an `HTTPException(400)` instead.

**Step 4 — PII scrubbing**: Replaces before sending to the LLM:
- Social Security Numbers (`XXX-XX-XXXX`) → `[SSN]`
- Credit card numbers (16-digit patterns) → `[CARD]`
- Email addresses → `[EMAIL]`

---

#### `security/output_guard.py`
Applied to the generated answer after the LLM produces it.

Redacts the same PII patterns from the output (with `REDACTED` suffix in labels):
- SSN → `[SSN REDACTED]`
- Credit card → `[CARD REDACTED]`
- Email → `[EMAIL REDACTED]`
- Phone numbers (`XXX-XXX-XXXX`) → `[PHONE REDACTED]`

This prevents the LLM from leaking PII that was present in the retrieved documents.

---

### 6.7 Prompts Layer

#### `prompts/templates.py`
All prompt strings for the RAG generation flow.

**`ROUTING_PROMPT`**: System prompt that tells GPT-4o to classify queries into exactly one of 5 categories. Response must be a single word (e.g. "factual").

**`_TYPE_INSTRUCTIONS`**: Per-query-type instructions injected into the system prompt:
- `FACTUAL`: "Provide a concise, direct answer with citations."
- `ANALYTICAL`: "Reason step-by-step over the evidence. Show your analysis before the conclusion."
- `CONVERSATIONAL`: "Respond naturally and conversationally. Keep it brief unless detail is needed."
- `CODE`: "Include working code examples. Explain key decisions. Use markdown code blocks."
- `MULTI_HOP`: "Explicitly chain the evidence: show how each fact leads to the next."

**`RAG_SYSTEM_BASE`**: The base system prompt:
```
"You are a precise, factual assistant. Answer questions using ONLY the provided context.
If the context does not contain enough information, say so explicitly — do not fabricate facts.
Always cite the source chunk IDs when you use information from them (e.g. [chunk-abc123]).
{type_instruction}"
```

**`build_rag_prompt()`**: Assembles the final prompt:
- Formats each chunk as: `[{chunk_id}] (source: {source})\n{content}`
- Prepends conversation history
- Returns `(system_prompt, user_message)` tuple

---

#### `prompts/grading.py`
**`RELEVANCE_GRADE_PROMPT`**: The system prompt used by `DocumentGrader` for each chunk evaluation. Gives GPT-4o a clear scoring rubric:
- 1.0 = directly answers the query
- 0.7–0.9 = highly relevant
- 0.4–0.6 = partially relevant
- 0.1–0.3 = tangentially related
- 0.0 = completely irrelevant

---

### 6.8 Tools Layer

#### `tools/web_search.py`
Web search fallback using the `ddgs` library (DuckDuckGo Search — no API key required).

**`search(query, max_results=5)`**: Async wrapper that runs the sync search in a thread pool to avoid blocking the event loop.

**`_sync_search(query, max_results)`**: The actual DuckDuckGo search logic:
1. Fetches `max_results * 3` candidates to account for filtered results
2. For each result:
   - Skip if no body text
   - Skip if URL already seen (exact deduplication)
   - Skip if non-English Wikipedia/wiki domain (e.g. `hi.wikipedia.org`, `fr.wikipedia.org`)
   - Skip if same domain already appears 2+ times
3. Assign position-based score: rank 1 = 0.95, rank 2 = 0.85, ..., floor at 0.50
4. Return clean `DocumentChunk` with domain as source label (e.g. `en.wikipedia.org`)

Each web result becomes a `DocumentChunk` that flows through the same generation pipeline as index documents — the LLM doesn't know (or care) whether content came from Qdrant or the web.

---

### 6.9 `seed_qdrant.py`
A one-time initialization script. Run it once to populate Qdrant with the 8 sample documents.

**What it does**:
1. Creates the `rag_documents` collection in Qdrant (768-dim, cosine distance)
2. Creates keyword payload indexes on `source`, `doc_type`, `language` fields (enables filtered search)
3. Embeds all 8 sample documents using `BAAI/bge-base-en-v1.5`
4. Upserts them into Qdrant as points with UUID IDs

**Sample documents indexed** (all technical content about the system itself):
- RAG overview
- Hybrid retrieval (RRF + dense + BM25)
- CRAG paper summary
- Qdrant documentation
- Semantic cache explanation
- Cross-encoder reranking
- FastAPI introduction
- Server-Sent Events (SSE)

---

### 6.10 `static/index.html`
Single-file frontend — no build step, no Node.js required.

**Tech stack**:
- Tailwind CSS (CDN)
- Vanilla JavaScript (no React/Vue)
- Google Fonts: Readex Pro

**UI Sections**:

1. **Hero section** — "securify" branded landing page with animated gradient background and "Start Asking" button that scrolls to the chat

2. **Chat tab** — the main interface:
   - Textarea for typing queries
   - Session ID field (for conversation identity)
   - Top-K slider (1–20)
   - Metadata filters (JSON)
   - Submit button
   - Chat message area that renders streamed tokens in real time
   - Citation cards under each answer (source, score, excerpt)
   - Grade badge (CORRECT / AMBIGUOUS / INCORRECT) and latency display

3. **Debug Search tab** — sends to `/api/search`, shows raw retrieval scores without generation. Useful for validating what the retriever finds.

**SSE streaming implementation**:
- Uses `EventSource` alternative via `fetch()` with `ReadableStream`
- Normalizes `\r\n` to `\n` before parsing (server sends CRLF)
- Handles multi-line `data:` fields (token events can span multiple lines if content has newlines)
- Parses `event: token` → append text; `event: citations` → render cards; `event: done` → finalize

---

## 7. Complete Request Flow — Step by Step

Let's trace a single query: **"What is RRF fusion?"** with `session_id="my-session"`.

```
1. HTTP POST /api/query/stream
   Body: { "query": "What is RRF fusion?", "session_id": "my-session", "top_k": 5 }

2. routes/query.py:
   - Generates trace_id = "abc-123-..."
   - InputGuard.sanitize("What is RRF fusion?")
     → no injection detected, no PII found
     → returns "What is RRF fusion?" unchanged

3. pipeline.stream() begins

4. ConversationMemory.rewrite_query("my-session", "What is RRF fusion?", llm)
   → No history yet (first turn)
   → Returns "What is RRF fusion?" unchanged

5. SemanticCache.get("What is RRF fusion?")
   → Encodes query to 768-dim vector
   → Loads all stored vectors from Redis
   → Computes cosine similarity against each
   → No match above 0.92 threshold
   → Returns None (cache miss)

6. QueryRouter.classify("What is RRF fusion?")
   → Calls GPT-4o with ROUTING_PROMPT
   → GPT-4o responds: "factual"
   → Returns QueryType.FACTUAL
   → top_k multiplier = 1
   → retrieval_k = 5 * 1 = 5

7. HybridRetriever.retrieve("What is RRF fusion?", top_k=20, filters={})

   7a. Dense retrieval:
       → Encode "What is RRF fusion?" → 768-dim vector
       → Qdrant cosine search → returns top-20 scored points
       → Highest match: hybrid_retrieval.md (contains "Reciprocal Rank Fusion")

   7b. Sparse retrieval (BM25):
       → Tokenize: ["what", "is", "rrf", "fusion"]
       → BM25 scores all 8 documents
       → Highest: hybrid_retrieval.md (contains "rrf" keyword)

   7c. RRF fusion:
       → hybrid_retrieval.md ranks #1 in both → gets highest RRF score
       → Returns merged, sorted list of 20 chunks

8. Reranker.rerank("What is RRF fusion?", chunks, top_k=5)
   → Cross-encoder scores each (query, chunk) pair
   → hybrid_retrieval.md scores ~8.5 (high positive score)
   → Other unrelated chunks score negative
   → Returns top-5 by reranker score

9. DocumentGrader.grade("What is RRF fusion?", top_5_chunks)
   → For each chunk, GPT-4o rates relevance 0.0–1.0
   → hybrid_retrieval.md → 0.95 (directly answers)
   → Other chunks → 0.1–0.3 (unrelated)
   → relevant count = 1 (≥ 0.6 threshold)
   → Grade = AMBIGUOUS (exactly 1 relevant chunk)
   → good_chunks = [hybrid_retrieval.md chunk]

10. AMBIGUOUS path → QueryDecomposer.decompose("What is RRF fusion?")
    → GPT-4o generates:
      ["What is Reciprocal Rank Fusion?",
       "How does RRF combine dense and sparse search results?",
       "What is the k constant in RRF?"]

11. CRAGAgent.retrieve_and_merge(sub_queries, filters={})
    → Runs HybridRetriever + Reranker for each sub-query in parallel
    → Sub-query 1 finds hybrid_retrieval.md (same chunk as before)
    → Sub-query 2 also finds hybrid_retrieval.md
    → After deduplication: only 1 unique chunk
    → Merges into good_chunks (deduplicated)

12. ConversationMemory.get_history("my-session") → [] (first turn)

13. build_rag_prompt("What is RRF fusion?", good_chunks, FACTUAL, history=[])
    → System: "You are a precise, factual assistant... Provide a concise, direct answer with citations."
    → User: "Context:\n[chunk-id] (source: hybrid_retrieval.md)\nHybrid retrieval fuses dense...\n\nQuestion: What is RRF fusion?"

14. GPT-4o streams response token by token:
    "Reciprocal Rank Fusion (RRF) is..."
    → Each token yielded as StreamEvent(event="token", data="Reciprocal")
    → Frontend appends each token to the chat bubble in real time

15. _extract_citations(good_chunks[:5])
    → Citation(text="Hybrid retrieval fuses dense...", source="hybrid_retrieval.md", score=8.5)

16. OutputGuard.redact(full_answer) → no PII found, answer unchanged

17. SemanticCache.set("What is RRF fusion?", full_answer)
    → Encodes query → stores vector + meta in Redis
    → Expires in 3600 seconds

18. ConversationMemory.add_turn("my-session", "user", "What is RRF fusion?")
    ConversationMemory.add_turn("my-session", "assistant", full_answer)

19. StreamEvent(event="citations", data=[...]) → sent to client
    StreamEvent(event="done", data={"cached": false, "grade": "ambiguous", "trace_id": "abc-123"}) → sent to client
```

---

## 8. CRAG Decision Tree

```
Retrieved N chunks from Qdrant
        │
        ▼
Grade each chunk with GPT-4o (0.0–1.0)
        │
        ├── relevant_count >= 2 ──────────────────► CORRECT
        │                                            → Use good chunks directly
        │                                            → Generate answer
        │
        ├── relevant_count == 1 ────────────────────► AMBIGUOUS
        │                                             → Decompose into 2-4 sub-queries
        │                                             → Re-retrieve for each sub-query
        │                                             → Merge + deduplicate
        │                                             → Generate answer from richer context
        │
        └── relevant_count == 0 ────────────────────► INCORRECT
                                                      → Web search (DuckDuckGo)
                                                      ├── Got results? → Generate from web chunks
                                                      └── No results? → Return "I couldn't find..."
```

**Important**: The INCORRECT and AMBIGUOUS paths are `if / elif` — they cannot both run. When web fallback succeeds after INCORRECT, the query does NOT enter the AMBIGUOUS decomposition path. Web results are used directly.

---

## 9. Data Models Reference

```
DocumentChunk
├── id: str                  UUID
├── content: str             Raw text
├── metadata: dict           {"source_type": "web"/"index", "url": "...", "doc_type": "..."}
├── score: float             Reranker score (index) OR position score (web: 0.50–0.95)
└── source: str              Display label

Citation
├── text: str                First 200 chars of the chunk
├── source: str              Where it came from
├── chunk_id: str            DocumentChunk.id
└── score: float             Relevance score

StreamEvent
├── event: str               "token" | "citations" | "done" | "error"
└── data: Any                str (token) | list[Citation] | dict | str

QueryRequest
├── query: str               1–2000 chars
├── session_id: str          Conversation identifier
├── top_k: int               1–20 (default 5)
├── filters: dict            Qdrant payload filters
└── stream: bool             Use SSE (default true)

QueryResponse
├── answer: str
├── citations: list[Citation] Max 5
├── query_type: QueryType
├── crag_grade: CRAGGrade
├── cached: bool
├── trace_id: str
└── latency_ms: float
```

---

## 10. Configuration Reference

All values can be set in `.env` file. Copy `.env.example` as a starting point.

```env
# Required
OPENAI_API_KEY=sk-proj-...

# Optional — defaults shown
LLM_MODEL=gpt-4o
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.0

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=rag_documents

REDIS_URL=redis://localhost:6379/0
SEMANTIC_CACHE_TTL=3600
SEMANTIC_CACHE_THRESHOLD=0.92
CONVERSATION_WINDOW=10

TOP_K_DENSE=20
TOP_K_SPARSE=20
TOP_K_RERANK=5
RRF_K=60

CRAG_RELEVANCE_THRESHOLD=0.6
CRAG_MAX_WEB_RESULTS=3

MAX_QUERY_LENGTH=2000
PII_REDACTION=true

# Observability (optional)
OPIK_API_KEY=
OPIK_PROJECT=production-rag
```

---

## 11. API Reference

### POST /api/query
Synchronous JSON response.

**Request**:
```json
{
  "query": "What is RRF?",
  "session_id": "user-123",
  "top_k": 5,
  "filters": {},
  "stream": false
}
```

**Response**:
```json
{
  "answer": "Reciprocal Rank Fusion (RRF) is...",
  "citations": [
    {
      "text": "Hybrid retrieval fuses dense...",
      "source": "hybrid_retrieval.md",
      "chunk_id": "abc-123",
      "score": 8.52
    }
  ],
  "query_type": "factual",
  "crag_grade": "correct",
  "cached": false,
  "trace_id": "xyz-456",
  "latency_ms": 2341.5
}
```

### POST /api/query/stream
SSE stream. Each event is a line pair:

```
event: token
data: Reciprocal Rank Fusion is a method...

event: token
data:  that combines ranked lists...

event: citations
data: [{"text":"...","source":"...","chunk_id":"...","score":8.5}]

event: done
data: {"cached":false,"grade":"correct","trace_id":"xyz-456"}
```

### POST /api/search
Debug endpoint — returns raw retrieval results.

**Request**: `{"query": "RRF", "top_k": 5, "filters": {}}`

**Response**: `{"chunks": [...DocumentChunk...], "latency_ms": 45.2}`

### GET /health
Returns component health status.

### GET /health/live
Returns `{"status": "alive"}`.

---

## 12. How Embeddings Work

An **embedding** is how text is converted into a number that a computer can compare mathematically.

1. Text input: `"Hybrid retrieval fuses dense and sparse search"`
2. The model (`BAAI/bge-base-en-v1.5`) processes this through a transformer neural network
3. Output: an array of 768 floating point numbers: `[0.12, -0.43, 0.87, 0.01, ...]`
4. This vector captures the **meaning** of the text in 768 dimensions

When you query "What is RRF?", the same model converts that to a 768-dim vector.

**Cosine similarity**: The similarity between two vectors is the cosine of the angle between them:
- 1.0 = identical direction (same meaning)
- 0.0 = perpendicular (unrelated)
- -1.0 = opposite direction (opposite meaning)

Qdrant finds the documents whose vectors are closest to the query vector — those are the most semantically relevant documents.

---

## 13. How Scoring Works

| Stage | Score meaning | Range |
|-------|--------------|-------|
| Qdrant cosine | How geometrically similar the embeddings are | 0.0–1.0 |
| BM25 | Keyword frequency relevance | 0.0–∞ (unnormalized) |
| RRF | Combined rank-based score | ~0.008–0.033 (1/(k+rank)) |
| Reranker (cross-encoder) | Query-document joint relevance | Unbounded, typically -5 to +10 |
| CRAG grader | GPT-4o's relevance rating | 0.0–1.0 |
| Web search | Position-based: rank 1=0.95, rank 2=0.85... | 0.50–0.95 |

After reranking, the reranker score replaces all earlier scores. This is what appears in citations.

---

## 14. Knowledge Base — What Data Is Indexed

Currently, Qdrant contains 8 short technical documents about the system itself. All are seeded by `seed_qdrant.py`:

| Source label | Topic |
|-------------|-------|
| `rag_overview.md` | What RAG is and how it works |
| `hybrid_retrieval.md` | Dense + BM25 + RRF explained |
| `crag_paper.md` | CRAG self-correction loop |
| `qdrant_docs.md` | Qdrant vector database overview |
| `semantic_cache.md` | Semantic caching with cosine similarity |
| `reranking.md` | Cross-encoder reranking vs bi-encoders |
| `fastapi_intro.md` | FastAPI framework overview |
| `sse_streaming.md` | Server-Sent Events protocol |

Anything outside these 8 topics will receive `grade=INCORRECT` and fall back to web search.

---

## 15. How to Add Your Own Data

### Option A: Add to seed_qdrant.py

Edit the `SAMPLE_DOCS` list in `seed_qdrant.py`:

```python
{
    "content": "Your document text goes here. The more context the better.",
    "source": "my_document.md",        # appears in citations
    "doc_type": "technical",           # for metadata filtering
    "language": "en",
},
```

Then re-run:
```bash
python seed_qdrant.py
```

### Option B: POST directly to Qdrant

For production, build an ingestion endpoint that:
1. Accepts a file upload (PDF, DOCX, TXT)
2. Extracts text
3. Splits into chunks (langchain-text-splitters is already a dependency)
4. Embeds each chunk with the BGE model
5. Upserts into Qdrant

The `pyproject.toml` already includes `pypdf2`, `pdfplumber`, `python-docx`, `langchain-text-splitters`, `tiktoken` for this purpose.

---

## 16. Running the System Locally

### Prerequisites
```bash
# Start infrastructure
docker run -d -p 6333:6333 qdrant/qdrant
docker run -d -p 6379:6379 redis

# Create .env
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-proj-...
```

### Install and seed
```bash
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install -e .

# Seed Qdrant with the 8 sample documents (run once)
python seed_qdrant.py
```

### Start the server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Test it
```bash
# Health check
curl http://localhost:8000/health

# Query (JSON)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "session_id": "test", "top_k": 5}'

# Debug search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "RRF", "top_k": 3}'

# Frontend
open http://localhost:8000
```

### Verify components
| URL | What you see |
|-----|-------------|
| `http://localhost:8000` | Frontend chat UI |
| `http://localhost:8000/health` | Component health JSON |
| `http://localhost:8000/docs` | Interactive API docs (development only) |
| `http://localhost:6333/dashboard` | Qdrant web UI |
