"""Prompt templates for the RAG pipeline."""
from __future__ import annotations
from app.models import DocumentChunk, QueryType

ROUTING_PROMPT = """You are a query classifier. Classify the user's query into exactly one of these categories:
- factual: direct fact lookup
- analytical: requires reasoning over multiple facts
- conversational: casual follow-up or chat
- code: programming or technical question
- multi_hop: requires chaining multiple pieces of information

Respond with ONLY the category name, lowercase, no punctuation."""

_TYPE_INSTRUCTIONS: dict[QueryType, str] = {
    QueryType.FACTUAL: "Provide a concise, direct answer with citations.",
    QueryType.ANALYTICAL: "Reason step-by-step over the evidence. Show your analysis before the conclusion.",
    QueryType.CONVERSATIONAL: "Respond naturally and conversationally. Keep it brief unless detail is needed.",
    QueryType.CODE: "Include working code examples. Explain key decisions. Use markdown code blocks.",
    QueryType.MULTI_HOP: "Explicitly chain the evidence: show how each fact leads to the next.",
}

RAG_SYSTEM_BASE = """You are a precise, factual assistant. Answer questions using ONLY the provided context.
If the context does not contain enough information, say so explicitly — do not fabricate facts.
Always cite the source chunk IDs when you use information from them (e.g. [chunk-abc123]).
{type_instruction}"""


def _format_chunks(chunks: list[DocumentChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        source = chunk.source or chunk.metadata.get("source", f"chunk-{i}")
        parts.append(f"[{chunk.id}] (source: {source})\n{chunk.content}")
    return "\n\n---\n\n".join(parts)


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history:
        role = turn.get("role", "user").upper()
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    return "\nConversation history:\n" + "\n".join(lines) + "\n"


def build_rag_prompt(
    query: str,
    chunks: list[DocumentChunk],
    query_type: QueryType,
    history: list[dict],
) -> tuple[str, str]:
    """Returns (system_prompt, user_message)."""
    type_instruction = _TYPE_INSTRUCTIONS.get(query_type, _TYPE_INSTRUCTIONS[QueryType.FACTUAL])
    system = RAG_SYSTEM_BASE.format(type_instruction=type_instruction)

    context_block = _format_chunks(chunks) if chunks else "No relevant context found."
    history_block = _format_history(history)

    user_msg = (
        f"{history_block}"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}"
    )
    return system, user_msg
