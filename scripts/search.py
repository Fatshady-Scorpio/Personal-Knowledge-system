#!/usr/bin/env python3
"""Search CLI — BM25-based wiki search engine.

Usage:
    # Build indexes for all domains
    PYTHONPATH=. python scripts/search.py --build

    # Quick search (retrieve entries, no LLM)
    PYTHONPATH=. python scripts/search.py "什么是 Transformer"

    # Full search with answer synthesis
    PYTHONPATH=. python scripts/search.py --answer "什么是 Transformer"

    # Search in specific domain
    PYTHONPATH=. python scripts/search.py --domain ai "什么是 Transformer"

    # Interactive search mode
    PYTHONPATH=. python scripts/search.py --interactive
"""

import argparse
import logging
import sys
from pathlib import Path

from src.search.search_engine import SearchEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
WIKI_ROOT = ROOT_DIR / "wiki"


def cmd_build(args, engine: SearchEngine):
    """Build/rebuild all domain indexes."""
    print("🔨 正在构建索引...")
    results = engine.build_indexes()
    for domain, count in results.items():
        print(f"  ✅ {domain}: {count} 词条")
    total = sum(results.values())
    print(f"\n📊 总计: {total} 词条已索引")


def cmd_search(args, engine: SearchEngine):
    """Perform a wiki search."""
    query = " ".join(args.query)
    target_domain = args.domain or None

    if target_domain:
        engine.domain = target_domain

    result = engine.search(query, synthesize=args.answer)

    # Show routing info
    intent = result["intent"]
    print(f"🎯 领域: {intent.primary_domain} (置信度: {intent.confidence:.2f})")
    if intent.is_multi_domain:
        print(f"   次要领域: {', '.join(intent.secondary_domains)}")
    print()

    # Show retrieved entries
    print(f"📚 检索到 {result['entry_count']} 个词条:")
    for r in result["results"]:
        source_tag = "🔍" if r["source"] == "bm25" else "🔗"
        score_str = f"score={r['score']:.3f}" if r["score"] > 0 else "link expansion"
        print(f"  {source_tag} [[{r['name']}]] ({score_str})")

    # Show answer if synthesized
    if args.answer and result["answer"]:
        print(f"\n{'='*60}")
        print("💡 答案:")
        print(f"{'='*60}")
        print(result["answer"])
        print(f"{'='*60}")


def cmd_interactive(args, engine: SearchEngine):
    """Interactive search mode."""
    print("🔍 Wiki 搜索引擎（交互模式）")
    print("输入问题进行搜索，输入 'q' 退出")
    print("命令: /build 重建索引, /domain <name> 切换领域, /retrieve 仅检索")
    print()

    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in ("q", "quit", "exit"):
            break
        if query.startswith("/build"):
            cmd_build(args, engine)
            continue
        if query.startswith("/domain "):
            domain = query.split(" ", 1)[1].strip()
            engine.domain = domain
            print(f"✅ 已切换到领域: {domain}")
            continue
        if query.startswith("/retrieve"):
            q = query.split(" ", 1)[1].strip() if " " in query else input("查询: ")
            _do_retrieve(q, engine)
            continue

        # Default: full search with answer
        engine.domain = args.domain
        result = engine.search(query, synthesize=True)
        _print_search_result(result)


def _do_retrieve(query: str, engine: SearchEngine):
    """Retrieve and display entries without synthesis."""
    results = engine.retrieve_only(query)
    print(f"📚 检索到 {len(results)} 个词条:")
    for r in results:
        score_str = f"score={r['score']:.3f}" if r["score"] > 0 else "link"
        print(f"  [[{r['name']}]] ({score_str})")
        # Show first 200 chars
        content = r.get("content", "")[:200]
        print(f"    {content}...\n")


def _print_search_result(result: dict):
    """Print search result in a readable format."""
    intent = result["intent"]
    print(f"🎯 {intent.primary_domain} (置信度: {intent.confidence:.2f})")
    print(f"📚 {result['entry_count']} 个词条:")
    for r in result["results"]:
        source_tag = "🔍" if r["source"] == "bm25" else "🔗"
        print(f"  {source_tag} [[{r['name']}]]")

    if result["answer"]:
        print(f"\n💡 {result['answer']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Search wiki knowledge base with BM25",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/search.py "什么是 Transformer"
    python scripts/search.py --answer "什么是 Transformer"
    python scripts/search.py --domain ai "LLM 训练"
    python scripts/search.py --build
    python scripts/search.py --interactive
        """,
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Search query (omit for interactive mode)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build/rebuild all domain indexes",
    )
    parser.add_argument(
        "--answer",
        action="store_true",
        help="Generate LLM answer from results",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Enable DuckDuckGo fallback (requires VPN)",
    )
    parser.add_argument(
        "--domain",
        type=str,
        help="Search in specific domain",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.6-plus",
        help="Model for answer synthesis",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive search mode",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    engine = SearchEngine(
        wiki_root=WIKI_ROOT,
        model=args.model,
        domain=args.domain,
        use_web=args.web,
    )

    if args.build:
        cmd_build(args, engine)
    elif args.interactive or not args.query:
        cmd_interactive(args, engine)
    else:
        cmd_search(args, engine)


if __name__ == "__main__":
    main()
