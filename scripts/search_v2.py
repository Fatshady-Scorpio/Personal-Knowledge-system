#!/usr/bin/env python3
"""V2 vault search CLI.

Builds and searches indexes from /20_knowledge/domains/*.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from personal_knowledge.config import load_vault_config
from personal_knowledge.retrieve import V2IndexManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the V2 personal knowledge vault")
    parser.add_argument("query", nargs="*", help="Search query")
    parser.add_argument("--build", action="store_true", help="Build all V2 domain indexes")
    parser.add_argument("--domain", default="ai_agents", help="V2 domain name or legacy domain alias")
    parser.add_argument("--top-k", type=int, default=10, help="Maximum results")
    parser.add_argument("--config", default="config/vault.yaml", help="Vault config path")
    args = parser.parse_args()

    config = load_vault_config(path=Path(args.config))
    manager = V2IndexManager(config)

    if args.build:
        results = manager.build_all()
        for domain, count in results.items():
            print(f"{domain}: {count}")
        return

    query = " ".join(args.query).strip()
    if not query:
        parser.print_help()
        return

    index = manager.get_index(args.domain)
    results = index.search(query, top_k=args.top_k)
    for result in results:
        print(f"{result['score']:.3f}\t{result['name']}\t{result['path']}")


if __name__ == "__main__":
    main()
