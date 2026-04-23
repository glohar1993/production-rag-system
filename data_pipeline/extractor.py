"""Extracts and cleans text from downloaded PDFs, splitting by legal sections."""
from __future__ import annotations
import re
import structlog
from pathlib import Path

log = structlog.get_logger(__name__)

# Matches legal section/rule/article headings
_SECTION_RE = re.compile(
    r'\n\s*(?:'
    r'(?:Section|SECTION|Sec\.?)\s+\d+[\w\-\.]*'
    r'|(?:Rule|RULE)\s+\d+[\w\-\.]*'
    r'|(?:Article|ARTICLE)\s+\d+[\w\-\.]*'
    r'|(?:Chapter|CHAPTER)\s+[IVXLCDM\d]+'
    r'|(?:Schedule|SCHEDULE)\s+[IVXLCDM\d]+'
    r'|(?:Circular|CIRCULAR)\s+No[\.\s]\d+'
    r'|(?:Notification|NOTIFICATION)\s+No[\.\s]\d+'
    r'|(?:Clause|CLAUSE)\s+\d+'
    r')\s*[\.\-\:]',
    re.IGNORECASE,
)

# Noise patterns to remove
_NOISE_RE = [
    re.compile(r'Page\s+\d+\s+of\s+\d+', re.IGNORECASE),
    re.compile(r'GOVERNMENT OF INDIA', re.IGNORECASE),
    re.compile(r'MINISTRY OF FINANCE', re.IGNORECASE),
    re.compile(r'CENTRAL BOARD OF INDIRECT TAXES', re.IGNORECASE),
    re.compile(r'www\.\S+\.gov\.in'),
    re.compile(r'\f'),                 # form feeds
    re.compile(r'\n{4,}', re.MULTILINE),  # excessive blank lines → 2
]


def _clean(text: str) -> str:
    for pattern in _NOISE_RE:
        text = pattern.sub('\n\n', text)
    # Collapse multiple spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # Normalize newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_text(pdf_path: Path) -> str:
    """Extract full text from a PDF using pdfplumber."""
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text(x_tolerance=2, y_tolerance=2)
                if txt:
                    pages.append(txt)
        raw = "\n\n".join(pages)
        return _clean(raw)
    except Exception as exc:
        log.warning("pdf_extraction_failed", path=str(pdf_path), error=str(exc))
        return ""


def split_by_section(text: str, doc_name: str, min_chars: int = 200) -> list[dict]:
    """
    Split document text at section/rule/chapter headings.
    Returns list of {heading, content, section_number} dicts.
    """
    if not text:
        return []

    # Find all split points
    boundaries = [m.start() for m in _SECTION_RE.finditer(text)]

    if not boundaries:
        # No section headings found — treat entire doc as one chunk
        return [{"heading": doc_name, "content": text, "section_number": ""}]

    sections = []
    boundaries.append(len(text))  # sentinel

    for i, start in enumerate(boundaries[:-1]):
        end = boundaries[i + 1]
        chunk = text[start:end].strip()

        if len(chunk) < min_chars:
            continue

        # Extract the heading from the first line
        first_line = chunk.split('\n')[0].strip()
        sections.append({
            "heading": first_line[:120],
            "content": chunk,
            "section_number": _extract_section_number(first_line),
        })

    log.info("sections_extracted", doc=doc_name, count=len(sections))
    return sections


def _extract_section_number(heading: str) -> str:
    match = re.search(r'\d+[\w\-\.]*', heading)
    return match.group(0) if match else ""
