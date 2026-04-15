#!/usr/bin/env python3
"""手动触发编译脚本 - 快速编译待处理的 Raw 材料。

使用方法：
    PYTHONPATH=. python scripts/compile_raw.py --all

优化说明：
- 翻译：分块并行翻译，避免长文本超时
- 概念提取：使用更快的模型，减少等待时间
- 超时控制：更严格的超时设置，快速失败
- 并行编译：支持多文件并行处理（--workers 参数）
"""

import argparse
import logging
import sys
from pathlib import Path

from src.compiler.raw_processor import RawProcessor
from src.compiler.wiki_builder import WikiBuilder
from src.compiler.index_generator import IndexGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _format_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Format a progress bar string."""
    if total == 0:
        return ""
    percent = current * 100 // total
    filled = current * width // total
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({percent}%)"


def main():
    parser = argparse.ArgumentParser(
        description="Manually trigger compilation of raw materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Compile all pending files
    python scripts/compile_raw.py --all

    # Compile all files with parallel compilation (3 workers)
    python scripts/compile_raw.py --all --workers 3

    # Compile a single file
    python scripts/compile_raw.py --file raw/videos/video.md

    # Verbose output
    python scripts/compile_raw.py --all --verbose

    # Regenerate index only
    python scripts/compile_raw.py --regenerate
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Compile all pending raw materials",
    )

    parser.add_argument(
        "--file",
        type=str,
        help="Compile a specific raw file",
    )

    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate index.md only",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Maximum concurrent workers for parallel compilation (default: 1)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Wiki directories
    raw_dir = Path("/Users/samcao/Obsidian/wiki/raw")
    wiki_dir = Path("/Users/samcao/Obsidian/wiki/wiki")

    # Initialize components
    processor = RawProcessor(raw_dir)
    builder = WikiBuilder(processor, wiki_dir)
    index_gen = IndexGenerator(wiki_dir)

    total_created = 0

    # Regenerate index only
    if args.regenerate and not args.all and not args.file:
        print("📑  重新生成索引...")
        index_gen.generate()
        print("✅ 索引生成完成")
        sys.exit(0)

    if args.all:
        # Compile all pending
        pending = processor.list_all(status="raw")
        if not pending:
            print("ℹ️  没有待编译的文件")
            sys.exit(0)

        print(f"🔄 编译 {len(pending)} 个文件...")
        if args.workers > 1:
            print(f"   最大并发数：{args.workers}")
        print()

        def on_progress(current, total):
            """Progress callback with progress bar."""
            progress = _format_progress_bar(current, total)
            print(f"   {progress}")

        # Use parallel compilation if workers > 1
        created_paths = builder.compile_all_pending(
            max_workers=args.workers,
            on_progress=on_progress if args.workers > 1 else None
        )

        for path in created_paths:
            total_created += 1

        # Regenerate index
        print()
        print("📑 重新生成索引...")
        index_gen.generate()
        print(f"✅ 完成！共生成 {total_created} 个词条")

    elif args.file:
        # Compile specific file
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = raw_dir / file_path

        if not file_path.exists():
            print(f"❌ 文件不存在：{file_path}")
            sys.exit(1)

        print(f"🔄 编译单个文件：{file_path.name}")
        created = builder.compile(file_path)
        total_created = len(created)

        if created:
            print(f"✓ 生成 {total_created} 个词条:")
            for path in created:
                print(f"  - {path.name}")
            print()
            print("📑 重新生成索引...")
            index_gen.generate()
            print(f"✅ 完成！")
        else:
            print("⚠️  未生成任何词条（可能已编译或提取失败）")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
