"""Splits extracted sections into token-bounded chunks with overlap."""
from __future__ import annotations
import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

log = structlog.get_logger(__name__)

# 400 tokens per chunk, 80 token overlap
# ~400 tokens ≈ 300 words — fits comfortably in a Qdrant payload and LLM context
CHUNK_SIZE = 1500     # characters (≈ 400 tokens for English)
CHUNK_OVERLAP = 300   # characters (≈ 80 tokens)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def chunk_section(
    content: str,
    source_meta: dict,
    heading: str = "",
    section_number: str = "",
) -> list[dict]:
    """
    Split one section's text into overlapping chunks.
    Each chunk gets the full source metadata so it can be found and cited.
    """
    if not content.strip():
        return []

    raw_chunks = _splitter.split_text(content)
    result = []

    for i, chunk_text in enumerate(raw_chunks):
        if len(chunk_text.strip()) < 100:
            continue

        # Prepend heading to every chunk so it's self-contained
        prefix = f"{heading}\n\n" if heading and i == 0 else ""
        final_text = (prefix + chunk_text).strip()

        result.append({
            "content": final_text,
            "metadata": {
                "source": source_meta.get("name", "gst_document"),
                "doc_type": source_meta.get("doc_type", "gst_knowledge"),
                "category": source_meta.get("category", "general"),
                "tags": source_meta.get("tags", []),
                "section_number": section_number,
                "heading": heading[:200],
                "chunk_index": i,
                "language": "en",
            },
        })

    return result


def chunk_document(sections: list[dict], source_meta: dict) -> list[dict]:
    """Chunk all sections of a document."""
    all_chunks = []
    for section in sections:
        chunks = chunk_section(
            content=section["content"],
            source_meta=source_meta,
            heading=section.get("heading", ""),
            section_number=section.get("section_number", ""),
        )
        all_chunks.extend(chunks)

    log.info("document_chunked",
             doc=source_meta.get("name"),
             sections=len(sections),
             chunks=len(all_chunks))
    return all_chunks


def chunk_static(static_docs: list[dict]) -> list[dict]:
    """Chunk the hardcoded static knowledge entries (already well-sized)."""
    result = []
    for doc in static_docs:
        chunks = chunk_section(
            content=doc["content"],
            source_meta=doc,
            heading=doc.get("source", ""),
        )
        result.extend(chunks)
    return result
