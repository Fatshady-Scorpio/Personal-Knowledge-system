#!/usr/bin/env python3
"""Compile one V2 source into maintained knowledge entries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from personal_knowledge.compile import JsonFileConceptExtractor, LLMConceptExtractor, V2SourceCompiler
from personal_knowledge.config import load_vault_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile one V2 source into knowledge entries")
    parser.add_argument("--source", required=True, help="Source markdown path")
    parser.add_argument("--concepts", help="Optional concept JSON path; if omitted, use LLM extractor")
    parser.add_argument("--config", default="config/vault.yaml", help="Vault config path")
    parser.add_argument("--model", default="qwen3.6-plus", help="Model for LLM extraction")
    parser.add_argument("--force", action="store_true", help="Compile even when source status is already compiled")
    args = parser.parse_args()

    config = load_vault_config(Path(args.config))
    extractor = JsonFileConceptExtractor(Path(args.concepts)) if args.concepts else LLMConceptExtractor(model=args.model)
    result = V2SourceCompiler(config=config, extractor=extractor).compile(Path(args.source), force=args.force)
    print(
        json.dumps(
            {
                "status": result.status,
                "source_path": str(result.source_path),
                "domain": result.domain,
                "created_paths": [str(path) for path in result.created_paths],
                "created_count": len(result.created_paths),
                "indexed_count": result.indexed_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
