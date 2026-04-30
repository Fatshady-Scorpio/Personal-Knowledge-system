#!/usr/bin/env python3
"""Migrate flat wiki entries to domain-organized structure.

Reads existing wiki entries from wiki/concepts/ and wiki/topics/,
classifies them into domains, and moves them to wiki/domains/{domain}/.

Usage:
    PYTHONPATH=. python scripts/migrate_to_domains.py [--dry-run]

Options:
    --dry-run    Show what would be moved without actually moving files
"""

import argparse
import logging
from pathlib import Path

from src.domain_manager import DomainManager, ROOT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Migrate wiki entries to domain structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without moving files")
    args = parser.parse_args()

    dm = DomainManager()
    wiki_dir = ROOT_DIR / "wiki"
    old_concepts = wiki_dir / "concepts"
    old_topics = wiki_dir / "topics"

    if not old_concepts.exists():
        print("No wiki/concepts/ directory found. Already migrated or no entries.")
        return

    # Collect all existing files
    all_files = list(old_concepts.glob("*.md")) + list(old_topics.glob("*.md"))
    print(f"Found {len(all_files)} wiki entries to migrate.\n")

    if not all_files:
        print("No entries to migrate.")
        return

    # Classify and plan
    migration_plan: dict[str, list[Path]] = {}
    for filepath in sorted(all_files):
        domain_id = dm.classify_entry(filepath)
        migration_plan.setdefault(domain_id, []).append(filepath)

    # Print migration report
    print("=" * 60)
    print("Migration Plan")
    print("=" * 60)
    total = 0
    for domain_id, files in sorted(migration_plan.items()):
        domain = dm.get_domain(domain_id)
        name = domain.name if domain else domain_id
        print(f"\n  {name} ({domain_id}): {len(files)} entries")
        for f in files[:5]:
            print(f"    - {f.name}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
        total += len(files)
    print(f"\n  Total: {total} entries")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] No files were moved. Run without --dry-run to execute.")
        return

    # Confirm
    confirm = input("\nProceed with migration? (y/N): ").strip().lower()
    if confirm != "y":
        print("Migration cancelled.")
        return

    # Execute migration
    moved_count = 0
    for domain_id, files in migration_plan.items():
        domain = dm.get_domain(domain_id)
        if not domain:
            logger.warning(f"Domain not found: {domain_id}, creating...")
            dm.add_domain(domain_id, domain_id, [], [])
            domain = dm.get_domain(domain_id)

        dm.ensure_dirs(domain_id)

        for filepath in files:
            if "concepts" in str(filepath):
                dest = domain.concepts_dir / filepath.name
            else:
                dest = domain.topics_dir / filepath.name

            dest.parent.mkdir(parents=True, exist_ok=True)
            filepath.rename(dest)
            moved_count += 1

        logger.info(f"Migrated {len(files)} entries to {domain.name}")

    print(f"\nMigration complete: {moved_count} entries moved.")
    print("\nNext steps:")
    print("  1. Run: PYTHONPATH=. python scripts/domain_manager.py status")
    print("  2. Review classification and adjust if needed")
    print("  3. Run: PYTHONPATH=. python scripts/compile_raw.py --all --regenerate-index")


if __name__ == "__main__":
    main()
