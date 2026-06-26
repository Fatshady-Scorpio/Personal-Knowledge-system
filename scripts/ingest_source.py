#!/usr/bin/env python3
"""Write a source into the V2 personal knowledge vault."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from personal_knowledge.config import load_vault_config
from personal_knowledge.ingest import SourceWriteRequest, SourceWriter


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a source into the V2 personal knowledge vault")
    parser.add_argument("--payload", required=True, help="JSON payload path")
    parser.add_argument("--config", default="config/vault.yaml", help="Vault config path")
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    config = load_vault_config(Path(args.config))
    result = SourceWriter(config).write(SourceWriteRequest(**payload))
    print(
        json.dumps(
            {
                "status": result.status,
                "path": str(result.path),
                "source_id": result.source_id,
                "content_hash": result.content_hash,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
