#!/usr/bin/env python3
"""Run reviewable V2 vault maintenance checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from personal_knowledge.config import load_vault_config
from personal_knowledge.maintenance.lint import VaultLinter, render_maintenance_markdown


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V2 vault maintenance checks")
    parser.add_argument("--config", default="config/vault.yaml", help="Vault config path")
    parser.add_argument("--no-write-report", action="store_true", help="Do not write the Markdown latest report")
    args = parser.parse_args()

    config = load_vault_config(Path(args.config))
    report = VaultLinter(config.vault_root).run()
    report_path = None
    if not args.no_write_report:
        report_path = config.system_dir / "reports" / "knowledge_maintenance_latest.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_maintenance_markdown(report, config.vault_root), encoding="utf-8")
    print(
        json.dumps(
            {
                "issues": [asdict(issue) for issue in report.issues],
                "issue_count": len(report.issues),
                "report_path": str(report_path) if report_path else None,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )


if __name__ == "__main__":
    main()
