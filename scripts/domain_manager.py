#!/usr/bin/env python3
"""Domain Manager CLI — manage knowledge domains.

Usage:
    PYTHONPATH=. python scripts/domain_manager.py status
    PYTHONPATH=. python scripts/domain_manager.py add --name "Health" --keywords "健康,医疗" --tags "健康,医疗"
    PYTHONPATH=. python scripts/domain_manager.py merge --from gaming --to general
    PYTHONPATH=. python scripts/domain_manager.py reclassify --domain general
"""

import argparse
import json
import logging
from pathlib import Path

from src.domain_manager import DomainManager, ROOT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def cmd_status(dm: DomainManager) -> None:
    """Show status of all domains."""
    status = dm.status()
    total_concepts = 0
    total_topics = 0

    print(f"\n{'='*60}")
    print(f"  Domain Status")
    print(f"{'='*60}")

    for domain_id, info in sorted(status.items()):
        marker = "[ON]" if info["enabled"] else "[OFF]"
        print(f"\n  {marker} {info['name']} ({domain_id})")
        print(f"      Concepts: {info['concepts']}")
        print(f"      Topics:   {info['topics']}")
        print(f"      Keywords: {info['keywords']}")
        print(f"      Tags:     {info['tags']}")
        total_concepts += info["concepts"]
        total_topics += info["topics"]

    print(f"\n{'─'*60}")
    print(f"  Total: {total_concepts} concepts, {total_topics} topics")
    print(f"{'='*60}\n")


def cmd_add(dm: DomainManager, args: argparse.Namespace) -> None:
    """Add a new domain."""
    domain_id = args.name.lower().replace(" ", "_")
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else []
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    domain = dm.add_domain(domain_id, args.name, keywords, tags)
    print(f"Added domain: {domain.name} ({domain_id})")
    print(f"  Keywords: {keywords}")
    print(f"  Tags:     {tags}")
    print(f"  Dir:      {domain.dir_path}")


def cmd_remove(dm: DomainManager, args: argparse.Namespace) -> None:
    """Remove a domain, moving entries to another."""
    dm.remove_domain(args.name, args.move_to)
    print(f"Removed domain: {args.name}")
    print(f"  Entries moved to: {args.move_to}")


def cmd_merge(dm: DomainManager, args: argparse.Namespace) -> None:
    """Merge one domain into another."""
    from_name = dm.get_domain(args.source)
    to_name = dm.get_domain(args.target)

    if not from_name:
        print(f"Source domain not found: {args.source}")
        return
    if not to_name:
        print(f"Target domain not found: {args.target}")
        return

    confirm = input(f"Merge '{from_name.name}' into '{to_name.name}'? This is irreversible. (y/N): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    dm.merge_domains(args.source, args.target)
    print(f"Merged '{from_name.name}' into '{to_name.name}'")


def cmd_reclassify(dm: DomainManager, args: argparse.Namespace) -> None:
    """Re-classify entries in a domain."""
    domain = dm.get_domain(args.domain)
    if not domain:
        print(f"Domain not found: {args.domain}")
        return
    if not domain.concepts_dir.exists():
        print(f"No concepts directory for: {args.domain}")
        return

    files = list(domain.concepts_dir.glob("*.md"))
    print(f"Re-classifying {len(files)} entries from {domain.name}...")

    reclassified = 0
    for filepath in files:
        new_domain = dm.classify_entry(filepath)
        if new_domain != args.domain:
            target = dm.get_domain(new_domain)
            if target:
                dest = target.concepts_dir / filepath.name
                dm.ensure_dirs(new_domain)
                filepath.rename(dest)
                reclassified += 1

    print(f"Re-classified {reclassified} entries out of {len(files)}")


def cmd_list_unclassified(dm: DomainManager) -> None:
    """List entries that are not in any domain directory."""
    wiki_dir = ROOT_DIR / "wiki"
    old_concepts = wiki_dir / "concepts"
    old_topics = wiki_dir / "topics"

    unclassified = []
    if old_concepts.exists():
        unclassified.extend(old_concepts.glob("*.md"))
    if old_topics.exists():
        unclassified.extend(old_topics.glob("*.md"))

    if not unclassified:
        print("All entries are already in domain directories.")
        return

    print(f"Found {len(unclassified)} unclassified entries:\n")
    for f in sorted(unclassified):
        domain_id = dm.classify_entry(f)
        domain = dm.get_domain(domain_id)
        name = domain.name if domain else domain_id
        print(f"  {f.name} → {name}")


def main():
    parser = argparse.ArgumentParser(description="Manage knowledge domains")
    subparsers = parser.add_subparsers(dest="command")

    # status
    subparsers.add_parser("status", help="Show domain status")

    # add
    add_p = subparsers.add_parser("add", help="Add a new domain")
    add_p.add_argument("--name", required=True, help="Domain display name")
    add_p.add_argument("--keywords", default="", help="Comma-separated keywords")
    add_p.add_argument("--tags", default="", help="Comma-separated tags")

    # remove
    rm_p = subparsers.add_parser("remove", help="Remove a domain")
    rm_p.add_argument("name", help="Domain ID to remove")
    rm_p.add_argument("--move-to", default="general", help="Domain to move entries to")

    # merge
    merge_p = subparsers.add_parser("merge", help="Merge one domain into another")
    merge_p.add_argument("--from", dest="source", required=True, help="Source domain ID")
    merge_p.add_argument("--to", dest="target", required=True, help="Target domain ID")

    # reclassify
    rc_p = subparsers.add_parser("reclassify", help="Re-classify entries in a domain")
    rc_p.add_argument("--domain", required=True, help="Domain ID to re-classify")

    # list-unclassified
    subparsers.add_parser("list-unclassified", help="List entries not in domain directories")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    dm = DomainManager()

    if args.command == "status":
        cmd_status(dm)
    elif args.command == "add":
        cmd_add(dm, args)
    elif args.command == "remove":
        cmd_remove(dm, args)
    elif args.command == "merge":
        cmd_merge(dm, args)
    elif args.command == "reclassify":
        cmd_reclassify(dm, args)
    elif args.command == "list-unclassified":
        cmd_list_unclassified(dm)


if __name__ == "__main__":
    main()
