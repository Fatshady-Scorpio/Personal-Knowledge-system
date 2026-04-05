#!/usr/bin/env python3
"""Query knowledge base using hybrid search (BM25 + local semantic)."""

import argparse
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(description="Query knowledge base")
    parser.add_argument("query", nargs="?", help="Search query or question")
    parser.add_argument("--bm25-only", action="store_true", help="Use BM25 only (no semantic)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--bm25-weight", type=float, default=None, help="BM25 weight (default: 0.7)")
    parser.add_argument("--semantic-weight", type=float, default=None, help="Semantic weight (default: 0.3)")
    args = parser.parse_args()

    config = get_config()
    knowledge_root = config.paths.get("knowledge_root", "./knowledge")

    # Use hybrid search (local)
    from src.retriever.hybrid_search import HybridSearch

    # Get weights from args or config
    bm25_weight = args.bm25_weight or config.settings.get("retriever", {}).get("local", {}).get("bm25_weight", 0.7)
    semantic_weight = args.semantic_weight or config.settings.get("retriever", {}).get("local", {}).get("semantic_weight", 0.3)

    # Normalize weights
    total = bm25_weight + semantic_weight
    bm25_weight = bm25_weight / total
    semantic_weight = semantic_weight / total

    print(f"Using hybrid search (BM25: {bm25_weight:.2f}, Semantic: {semantic_weight:.2f})...")

    # If BM25 only, disable semantic
    use_semantic = not args.bm25_only

    search = HybridSearch(
        knowledge_root=knowledge_root,
        use_semantic=use_semantic,
        bm25_weight=bm25_weight,
        semantic_weight=semantic_weight
    )

    # Build index if needed
    count = search.build_index()
    print(f"Index loaded ({count} documents)")
    print()

    results = search.search(args.query, top_k=args.top_k, use_hybrid=use_semantic)
    print(f"\n找到 {len(results)} 个结果:\n")
    for r in results:
        score = r.get("combined_score", r.get("score", 0))
        print(f"[{score:.3f}] {r['title']}")
        print(f"    {r['content_preview'][:100]}...")
        if use_semantic:
            print(f"    BM25: {r.get('bm25_score', 0):.3f} | Semantic: {r.get('semantic_score', 0):.3f}")
        print()


if __name__ == "__main__":
    main()
