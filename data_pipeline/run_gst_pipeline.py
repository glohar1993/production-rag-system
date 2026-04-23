"""
GST Data Pipeline — main entry point.

Run:
    python data_pipeline/run_gst_pipeline.py

What it does:
  1. Downloads all public CBIC GST PDFs (skips if already cached locally).
  2. Extracts text from each PDF.
  3. Splits into section-level chunks.
  4. Indexes static knowledge (built-in, no download needed).
  5. Embeds everything with BGE and upserts into Qdrant.

After running, ask the RAG system any GST question —
it will answer from real CBIC documents with section citations.
"""
from __future__ import annotations
import asyncio
import sys
import time
import structlog

log = structlog.get_logger(__name__)


async def run_pipeline(skip_pdfs: bool = False) -> None:
    from data_pipeline.gst_sources import GST_SOURCES, GST_STATIC_KNOWLEDGE
    from data_pipeline.fetcher import fetch_all
    from data_pipeline.extractor import extract_text, split_by_section
    from data_pipeline.chunker import chunk_document, chunk_static
    from data_pipeline.indexer import index_chunks

    start = time.perf_counter()
    all_chunks: list[dict] = []

    # ── Step 1: Static knowledge (always indexed) ─────────────────────────────
    print("\n[1/4] Indexing built-in GST knowledge base...")
    static_chunks = chunk_static(GST_STATIC_KNOWLEDGE)
    print(f"      → {len(static_chunks)} chunks from {len(GST_STATIC_KNOWLEDGE)} knowledge entries")
    all_chunks.extend(static_chunks)

    # ── Step 2: Download PDFs ─────────────────────────────────────────────────
    if not skip_pdfs:
        print(f"\n[2/4] Downloading {len(GST_SOURCES)} public CBIC documents...")
        downloaded = await fetch_all(GST_SOURCES, concurrency=3)
        print(f"      → Downloaded {len(downloaded)}/{len(GST_SOURCES)} documents")
    else:
        print("\n[2/4] Skipping PDF download (--skip-pdfs flag set)")
        downloaded = []

    # ── Step 3: Extract + chunk PDFs ─────────────────────────────────────────
    if downloaded:
        print(f"\n[3/4] Extracting text and chunking {len(downloaded)} PDFs...")
        for source_meta, pdf_path in downloaded:
            print(f"      Processing: {source_meta['name']}")
            text = extract_text(pdf_path)
            if not text:
                print(f"      ⚠ Could not extract text from {source_meta['name']}")
                continue

            sections = split_by_section(text, source_meta["name"])
            chunks = chunk_document(sections, source_meta)
            all_chunks.extend(chunks)
            print(f"      → {len(sections)} sections → {len(chunks)} chunks")
    else:
        print("\n[3/4] No PDFs to process")

    # ── Step 4: Index into Qdrant ─────────────────────────────────────────────
    print(f"\n[4/4] Indexing {len(all_chunks)} total chunks into Qdrant...")
    print("      (This may take a few minutes — embedding with BGE model)")

    indexed = index_chunks(all_chunks)

    elapsed = time.perf_counter() - start
    print(f"\n{'='*60}")
    print(f"  GST Pipeline Complete!")
    print(f"  Chunks indexed : {indexed}")
    print(f"  Time taken     : {elapsed:.1f} seconds")
    print(f"{'='*60}")
    print("\nYou can now ask any GST question to the RAG system.")
    print("Examples:")
    print("  - What is the ITC rule for motor vehicles?")
    print("  - What are the GST rates for textile goods?")
    print("  - When is RCM applicable on GTA services?")
    print("  - What is the due date for GSTR-9?")
    print("  - How does inverted duty structure refund work?")


if __name__ == "__main__":
    skip = "--skip-pdfs" in sys.argv
    asyncio.run(run_pipeline(skip_pdfs=skip))
