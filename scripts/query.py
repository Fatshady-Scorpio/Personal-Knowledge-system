#!/usr/bin/env python3
"""Query knowledge base using semantic search."""

import argparse
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.retriever.rag_qa import RAGQA
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(description="Query knowledge base")
    parser.add_argument("query", nargs="?", help="Search query or question")
    parser.add_argument("--qa", action="store_true", help="Use RAG QA mode")
    parser.add_argument("--local", action="store_true", help="Use local BM25 mode")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid search (BM25 + semantic)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--index", help="Path to index")
    args = parser.parse_args()

    config = get_config()
    knowledge_root = config.paths.get("knowledge_root", "./knowledge")

    # Local mode
    if args.local or args.hybrid:
        from src.retriever.hybrid_search import HybridSearch

        print(f"Using {'hybrid' if args.hybrid else 'BM25'} search mode...")
        search = HybridSearch(
            knowledge_root=knowledge_root,
            use_semantic=args.hybrid
        )

        # Build index if needed
        search.build_index()

        results = search.search(args.query, top_k=args.top_k, use_hybrid=args.hybrid)
        print(f"\n找到 {len(results)} 个结果:\n")
        for r in results:
            score = r.get("combined_score", r.get("score", 0))
            print(f"[{score:.2f}] {r['title']}")
            print(f"    {r['content_preview'][:100]}...")
            if args.hybrid:
                print(f"    BM25: {r.get('bm25_score', 0):.2f} | Semantic: {r.get('semantic_score', 0):.2f}")
            print()

    # Cloud mode (original)
    elif args.qa:
        embedder = Embedder(api_key=config.bailian_api_key)
        index_path = args.index or config.settings.get("retriever", {}).get(
            "index_path", "./knowledge/index"
        )
        vector_store = VectorStore(index_path=index_path)

        qa = RAGQA(embedder=embedder, vector_store=vector_store)
        result = qa.answer(args.query, top_k=args.top_k)
        print(f"\n答案：{result['answer']}\n")
        if result['sources']:
            print("资料来源:")
            for s in result['sources']:
                print(f"  - {s['title']} (score: {s['score']:.2f})")
    else:
        embedder = Embedder(api_key=config.bailian_api_key)
        index_path = args.index or config.settings.get("retriever", {}).get(
            "index_path", "./knowledge/index"
        )
        vector_store = VectorStore(index_path=index_path)

        search = SemanticSearch(
            embedder=embedder,
            vector_store=vector_store,
            knowledge_root=knowledge_root
        )
        results = search.search(args.query, top_k=args.top_k)
        print(f"\n找到 {len(results)} 个结果:\n")
        for r in results:
            print(f"[{r['score']:.2f}] {r['title']}")
            print(f"    {r['content_preview'][:100]}...")
            print()


if __name__ == "__main__":
    main()
