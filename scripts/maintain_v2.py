#!/usr/bin/env python3
"""Run reviewable V2 vault maintenance checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from personal_knowledge.config import load_vault_config
from personal_knowledge.maintenance.lint import VaultLinter


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V2 vault maintenance checks")
    parser.add_argument("--config", default="config/vault.yaml", help="Vault config path")
    args = parser.parse_args()

    config = load_vault_config(Path(args.config))
    report = VaultLinter(config.vault_root).run()
    print(json.dumps({"issues": [asdict(issue) for issue in report.issues]}, ensure_ascii=False, default=_json_default))


if __name__ == "__main__":
    main()
