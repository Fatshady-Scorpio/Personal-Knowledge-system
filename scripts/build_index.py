#!/usr/bin/env python3
"""Build semantic search index from knowledge base."""

import argparse
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(description="Build search index")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    parser.add_argument("--output", help="Output path for index")
    args = parser.parse_args()

    config = get_config()

    embedder = Embedder(api_key=config.bailian_api_key)
    index_path = args.output or config.settings.get("retriever", {}).get(
        "index_path", "./knowledge/index"
    )
    vector_store = VectorStore(index_path=index_path)

    search = SemanticSearch(
        embedder=embedder,
        vector_store=vector_store,
        knowledge_root=config.paths.get("knowledge_root", "./knowledge")
    )

    print("Building index...")
    count = search.build_index(rebuild=args.rebuild)
    print(f"Indexed {count} documents")
    print(f"Index saved to {index_path}")


if __name__ == "__main__":
    main()
