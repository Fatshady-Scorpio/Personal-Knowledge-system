#!/usr/bin/env python3
"""Compile raw materials into wiki entries.

Usage:
    PYTHONPATH=. python scripts/compile_raw.py [options]

Options:
    --all           Compile all pending raw materials
    --file PATH     Compile a specific raw material
    --regenerate    Regenerate index.md
    --verbose       Show detailed output
"""

import argparse
import logging
from pathlib import Path

from src.compiler.raw_processor import RawProcessor
from src.compiler.wiki_builder import WikiBuilder
from src.compiler.index_generator import IndexGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Compile raw materials to wiki entries")
    parser.add_argument("--all", action="store_true", help="Compile all pending materials")
    parser.add_argument("--file", type=str, help="Compile a specific file")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate index.md")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Wiki directories point to Obsidian vault (production data)
    raw_dir = Path("/Users/samcao/Obsidian/wiki/raw")
    wiki_dir = Path("/Users/samcao/Obsidian/wiki/wiki")

    # Initialize components
    raw_processor = RawProcessor(raw_dir)
    wiki_builder = WikiBuilder(raw_processor, wiki_dir)
    index_generator = IndexGenerator(wiki_dir)

    # Compile specified file or all pending
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = raw_dir / file_path

        logger.info(f"Compiling: {file_path}")
        created = wiki_builder.compile(file_path)
        logger.info(f"Created {len(created)} wiki entries")

    elif args.all:
        logger.info("Compiling all pending raw materials...")
        created = wiki_builder.compile_all_pending()
        logger.info(f"Created {len(created)} wiki entries")

    # Regenerate index if requested
    if args.regenerate or args.all:
        logger.info("Regenerating index.md...")
        index_path = index_generator.generate()
        logger.info(f"Generated index: {index_path}")

    logger.info("Compile complete!")


if __name__ == "__main__":
    main()
