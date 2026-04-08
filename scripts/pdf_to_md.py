#!/usr/bin/env python3
"""Convert PDF files to Markdown format for Agentic Wiki.

This script extracts text from PDF files and converts them to markdown
with proper frontmatter for compilation.

Dependencies:
    - PyPDF2 (pip install PyPDF2)
    - pdfplumber (pip install pdfplumber) - better text extraction

Usage:
    PYTHONPATH=. python scripts/pdf_to_md.py <pdf_file> [output_dir]

Examples:
    # Convert single PDF
    PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf

    # Convert to specific directory
    PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf /path/to/raw/papers

    # Convert with custom metadata
    PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf --title "My Paper" --tags "AI,LLM"
"""

import argparse
import logging
import re
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_text_with_pdfplumber(pdf_path: Path) -> list[str]:
    """Extract text using pdfplumber (better quality)."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                logger.warning(f"  No text extracted from page {i + 1}")
                pages.append(f"[Page {i + 1} - no text extracted]")
    return pages


def extract_text_with_pypdf2(pdf_path: Path) -> list[str]:
    """Extract text using PyPDF2 (fallback)."""
    pages = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                logger.warning(f"  No text extracted from page {i + 1}")
                pages.append(f"[Page {i + 1} - no text extracted]")
    return pages


def extract_text(pdf_path: Path) -> list[str]:
    """Extract text from PDF using best available method."""
    if HAS_PDFPLUMBER:
        logger.info("Using pdfplumber for text extraction...")
        return extract_text_with_pdfplumber(pdf_path)
    elif HAS_PYPDF2:
        logger.info("Using PyPDF2 for text extraction...")
        return extract_text_with_pypdf2(pdf_path)
    else:
        raise RuntimeError(
            "No PDF library available. Install with:\n"
            "  pip install pdfplumber  # Recommended\n"
            "  pip install PyPDF2      # Fallback"
        )


def extract_metadata(pdf_path: Path) -> dict:
    """Extract metadata from PDF file."""
    metadata = {}

    if HAS_PDFPLUMBER:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.metadata:
                metadata = pdf.metadata
    elif HAS_PYPDF2:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if reader.metadata:
                metadata = reader.metadata

    return metadata


def infer_title(pdf_path: Path, metadata: dict) -> str:
    """Infer title from PDF metadata or filename."""
    # Try metadata first
    for key in ["Title", "title", "/Title"]:
        if key in metadata and metadata[key]:
            return str(metadata[key]).strip()

    # Fall back to filename
    filename = pdf_path.stem
    # Remove date prefix if present (e.g., "20260408_")
    filename = re.sub(r"^\d{8}_", "", filename)
    # Replace underscores and hyphens with spaces
    filename = filename.replace("_", " ").replace("-", " ")
    # Capitalize
    return filename.strip().title()


def infer_tags(metadata: dict) -> list[str]:
    """Infer tags from PDF metadata."""
    tags = []

    # Try Keywords field
    for key in ["Keywords", "keywords", "/Keywords"]:
        if key in metadata and metadata[key]:
            keywords = str(metadata[key])
            tags = [k.strip() for k in keywords.split(",")]
            break

    # Add generic tag if no keywords found
    if not tags:
        tags.append("PDF")

    return tags


def build_markdown(
    title: str,
    content: str,
    source: str,
    tags: list[str],
    user_notes: str = None,
) -> str:
    """Build markdown content with frontmatter."""
    frontmatter = f"""---
type: article
title: {title}
source: {source}
collected_at: {datetime.now().isoformat()}
tags: {tags}
status: raw
---

# {title}

{content}
"""

    if user_notes:
        frontmatter += f"""
---

## 我的思考

{user_notes}
"""

    return frontmatter


def convert_pdf_to_md(
    pdf_path: Path,
    output_dir: Path = None,
    title: str = None,
    tags: list[str] = None,
    user_notes: str = None,
) -> Path:
    """Convert a PDF file to Markdown.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory (default: raw/papers/)
        title: Custom title (default: from PDF metadata or filename)
        tags: Custom tags (default: from PDF metadata or ["PDF"])
        user_notes: Optional user notes to append

    Returns:
        Path to the generated markdown file
    """
    logger.info(f"Converting: {pdf_path}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Set output directory
    if output_dir is None:
        # Default to Obsidian raw/papers/ directory
        output_dir = Path("/Users/samcao/Obsidian/wiki/raw/papers")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract metadata
    pdf_metadata = extract_metadata(pdf_path)

    # Determine title
    if title:
        final_title = title
    else:
        final_title = infer_title(pdf_path, pdf_metadata)

    # Determine tags
    if tags:
        final_tags = tags
    else:
        final_tags = infer_tags(pdf_metadata)

    # Extract text
    pages = extract_text(pdf_path)
    content = "\n\n".join(pages)

    # Build markdown
    md_content = build_markdown(
        title=final_title,
        content=content,
        source=f"file://{pdf_path.absolute()}",
        tags=final_tags,
        user_notes=user_notes,
    )

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_]", "_", final_title)[:50]
    output_filename = f"{timestamp}_{safe_title}.md"
    output_path = output_dir / output_filename

    # Write output
    output_path.write_text(md_content, encoding="utf-8")
    logger.info(f"Created: {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown for Agentic Wiki"
    )
    parser.add_argument(
        "pdf_file",
        type=Path,
        help="Path to the PDF file"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Output directory (default: /Users/samcao/Obsidian/wiki/raw/papers/)"
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title (default: from PDF metadata or filename)"
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags (default: from PDF metadata)"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Your notes/thoughts about this PDF"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required dependencies"
    )

    args = parser.parse_args()

    # Install dependencies if requested
    if args.install_deps:
        import subprocess
        subprocess.run(["pip", "install", "pdfplumber", "PyPDF2"])
        return

    # Parse tags
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",")]

    try:
        output_path = convert_pdf_to_md(
            pdf_path=args.pdf_file,
            output_dir=args.output_dir,
            title=args.title,
            tags=tags,
            user_notes=args.notes,
        )
        logger.info(f"\n✅ Done! Output: {output_path}")
        logger.info("\nNext steps:")
        logger.info("  1. Review the generated markdown file")
        logger.info("  2. Add your thoughts in the '我的思考' section if needed")
        logger.info("  3. The file will be compiled automatically by the scheduler")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise


if __name__ == "__main__":
    main()
