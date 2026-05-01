#!/usr/bin/env python3
"""Promote QA — CLI for knowledge weaving (Q&A → wiki).

Usage:
    # Weave all Q&A files
    PYTHONPATH=. python scripts/promote_qa.py

    # Weave a specific Q&A file
    PYTHONPATH=. python scripts/promote_qa.py --file outputs/qa/20260501_xxx.md

    # Weave with explicit domain
    PYTHONPATH=. python scripts/promote_qa.py --domain ai

    # Dry run (evaluate without creating entries)
    PYTHONPATH=. python scripts/promote_qa.py --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

from src.search.knowledge_weaver import KnowledgeWeaver, KnowledgeValue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
WIKI_ROOT = ROOT_DIR / "wiki"
QA_DIR = ROOT_DIR / "outputs" / "qa"


def _value_icon(value: KnowledgeValue) -> str:
    icons = {
        KnowledgeValue.HIGH: "🟢",
        KnowledgeValue.MEDIUM: "🟡",
        KnowledgeValue.LOW: "⚪",
    }
    return icons.get(value, "?")


def cmd_weave(args, weaver: KnowledgeWeaver):
    """Weave Q&A files into wiki."""
    if args.file:
        qa_path = Path(args.file)
        if not qa_path.is_absolute():
            qa_path = QA_DIR / qa_path

        if not qa_path.exists():
            print(f"❌ 文件不存在：{qa_path}")
            sys.exit(1)

        print(f"🔍 评估 Q&A：{qa_path.name}")
        if args.dry_run:
            _dry_run_single(weaver, qa_path, args.domain)
        else:
            result = weaver.weave_qa(qa_path, args.domain)
            _print_result(result)
    else:
        # Weave all pending
        if not QA_DIR.exists():
            print("ℹ️  没有 Q&A 文件")
            sys.exit(0)

        qa_files = list(QA_DIR.glob("*.md"))
        if not qa_files:
            print("ℹ️  没有待处理的 Q&A 文件")
            sys.exit(0)

        print(f"🔍 评估 {len(qa_files)} 个 Q&A 文件...")
        print()

        if args.dry_run:
            for qa_path in sorted(qa_files):
                _dry_run_single(weaver, qa_path, args.domain)
        else:
            results = weaver.weave_all_pending(args.domain)
            _print_summary(results)


def _dry_run_single(weaver: KnowledgeWeaver, qa_path: Path, domain: str):
    """Evaluate a Q&A file without weaving."""
    content = qa_path.read_text(encoding="utf-8")
    question, answer = weaver._parse_qa(content)

    if not question or not answer:
        print(f"  ⚪ {qa_path.name}: 解析失败")
        return

    value = weaver.evaluate_qa(question, answer)
    icon = _value_icon(value)
    action = {
        KnowledgeValue.HIGH: "→ 创建新词条",
        KnowledgeValue.MEDIUM: "→ 合并到现有词条",
        KnowledgeValue.LOW: "→ 保留为 QA 记录",
    }.get(value, "")

    print(f"  {icon} {qa_path.name}: {value.value} {action}")
    # Show question preview
    q_preview = question[:80] + "..." if len(question) > 80 else question
    print(f"     Q: {q_preview}")


def _print_result(result):
    """Print a single weaving result."""
    icon = _value_icon(result.value)
    print(f"\n{icon} 处理结果：")
    print(f"   等级: {result.value.value}")
    print(f"   操作: {result.action}")
    if result.target_path:
        print(f"   文件: {result.target_path}")
    if result.merged_into:
        print(f"   合并到: [[{result.merged_into}]]")


def _print_summary(results: list):
    """Print a summary of all weaving results."""
    if not results:
        print("✅ 没有可处理的 Q&A 文件")
        return

    high = sum(1 for r in results if r.value == KnowledgeValue.HIGH)
    medium = sum(1 for r in results if r.value == KnowledgeValue.MEDIUM)
    low = sum(1 for r in results if r.value == KnowledgeValue.LOW)

    print()
    print("=" * 50)
    print("📊 结网结果汇总")
    print("=" * 50)
    print(f"  🟢 高价值（新词条）: {high}")
    print(f"  🟡 中价值（合并）:   {medium}")
    print(f"  ⚪ 低价值（保留）:  {low}")
    print(f"  总计: {len(results)}")
    print()

    # Print individual results
    for r in results:
        icon = _value_icon(r.value)
        print(f"  {icon} {r.value.value}: {r.action}")


def main():
    parser = argparse.ArgumentParser(
        description="Promote Q&A to wiki entries (knowledge weaving)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run: see what would happen
    python scripts/promote_qa.py --dry-run

    # Weave all Q&A files
    python scripts/promote_qa.py

    # Weave with specific domain
    python scripts/promote_qa.py --domain ai
        """,
    )

    parser.add_argument(
        "--file",
        type=str,
        help="Process a specific Q&A file",
    )
    parser.add_argument(
        "--domain",
        type=str,
        help="Target domain (auto-detected if not specified)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate without creating/merging entries",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.6-plus",
        help="Model for concept extraction",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    weaver = KnowledgeWeaver(
        wiki_root=WIKI_ROOT,
        qa_dir=QA_DIR,
        model=args.model,
    )

    cmd_weave(args, weaver)


if __name__ == "__main__":
    main()
