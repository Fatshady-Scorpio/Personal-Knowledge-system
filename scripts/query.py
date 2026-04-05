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
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--index", help="Path to index")
    args = parser.parse_args()

    config = get_config()

    embedder = Embedder(api_key=config.bailian_api_key)
    index_path = args.index or config.settings.get("retriever", {}).get(
        "index_path", "./knowledge/index"
    )
    vector_store = VectorStore(index_path=index_path)

    if args.qa:
        qa = RAGQA(embedder=embedder, vector_store=vector_store)
        result = qa.answer(args.query, top_k=args.top_k)
        print(f"\n答案：{result['answer']}\n")
        if result['sources']:
            print("资料来源:")
            for s in result['sources']:
                print(f"  - {s['title']} (score: {s['score']:.2f})")
    else:
        search = SemanticSearch(
            embedder=embedder,
            vector_store=vector_store,
            knowledge_root=config.paths.get("knowledge_root", "./knowledge")
        )
        results = search.search(args.query, top_k=args.top_k)
        print(f"\n找到 {len(results)} 个结果:\n")
        for r in results:
            print(f"[{r['score']:.2f}] {r['title']}")
            print(f"    {r['content_preview'][:100]}...")
            print()


if __name__ == "__main__":
    main()
