from __future__ import annotations

import argparse
from pathlib import Path

from personal_knowledge.migration.inventory import collect_markdown_inventory
from personal_knowledge.migration.migrator import migrate_vault


CURRENT = Path("/Users/samcao/Obsidian/wiki")
STAGING = Path("/Users/samcao/Obsidian/wiki-v2-staging")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inventory", "dry-run", "migrate", "validate"])
    args = parser.parse_args()

    if args.command == "inventory":
        items = collect_markdown_inventory(CURRENT, ignored_dirs={".obsidian", ".trash"})
        print(f"markdown_files={len(items)}")
        return

    if args.command == "dry-run":
        report = migrate_vault(CURRENT, STAGING, dry_run=True)
        print(report)
        return

    if args.command == "migrate":
        report = migrate_vault(CURRENT, STAGING, dry_run=False)
        print(report)
        return

    if args.command == "validate":
        current_count = len(collect_markdown_inventory(CURRENT, ignored_dirs={".obsidian", ".trash"}))
        staging_count = len(collect_markdown_inventory(STAGING, ignored_dirs={".obsidian", ".trash", "_system"}))
        if current_count != staging_count:
            raise SystemExit(f"count mismatch current={current_count} staging={staging_count}")
        print("ok")


if __name__ == "__main__":
    main()
