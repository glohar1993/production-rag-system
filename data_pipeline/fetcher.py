"""Downloads PDF documents from public URLs."""
from __future__ import annotations
import asyncio
import hashlib
import structlog
from pathlib import Path
import httpx

log = structlog.get_logger(__name__)

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GSTBot/1.0; "
        "+https://github.com/glohar1993/production-rag-system)"
    )
}


async def fetch_pdf(url: str, name: str) -> Path | None:
    """Download a PDF from a public URL. Returns local path or None on failure."""
    filename = hashlib.md5(url.encode()).hexdigest()[:12] + ".pdf"
    dest = DOWNLOAD_DIR / filename

    if dest.exists():
        log.info("pdf_already_cached", name=name, path=str(dest))
        return dest

    log.info("downloading_pdf", name=name, url=url)
    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=60.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                log.warning("pdf_download_failed", name=name, status=resp.status_code, url=url)
                return None

            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and len(resp.content) < 1000:
                log.warning("pdf_not_found", name=name, content_type=content_type)
                return None

            dest.write_bytes(resp.content)
            log.info("pdf_downloaded", name=name, size_kb=len(resp.content) // 1024)
            return dest

    except Exception as exc:
        log.warning("pdf_download_error", name=name, url=url, error=str(exc))
        return None


async def fetch_all(sources: list[dict], concurrency: int = 3) -> list[tuple[dict, Path]]:
    """Download all sources with bounded concurrency. Returns (source_meta, local_path) pairs."""
    sem = asyncio.Semaphore(concurrency)
    results: list[tuple[dict, Path]] = []

    async def _fetch(source: dict):
        async with sem:
            path = await fetch_pdf(source["url"], source["name"])
            if path:
                results.append((source, path))

    await asyncio.gather(*[_fetch(s) for s in sources])
    log.info("fetch_complete", total=len(sources), downloaded=len(results))
    return results
