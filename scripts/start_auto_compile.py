#!/usr/bin/env python3
"""Start the auto-compile scheduler.

This monitors the raw/ directory and automatically compiles pending materials when:
1. A certain number of files accumulate (default: 5)
2. A certain time period has passed (default: 24 hours)

Usage:
    PYTHONPATH=. python scripts/start_auto_compile.py [options]

Options:
    --min-files N     Minimum files to trigger compilation (default: 5)
    --max-wait HOURS  Maximum hours to wait (default: 24)
    --check-every M   Check interval in minutes (default: 30)
    --run-once        Run compilation once and exit
    --verbose         Show detailed output
"""

import argparse
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

from src.compiler.auto_compile_scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Start auto-compile scheduler for Agentic Wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start with defaults (5 files or 24 hours)
    python scripts/start_auto_compile.py

    # Compile after 3 files accumulate
    python scripts/start_auto_compile.py --min-files 3

    # Check every 15 minutes
    python scripts/start_auto_compile.py --check-every 15

    # Run compilation once and exit
    python scripts/start_auto_compile.py --run-once
        """,
    )

    parser.add_argument(
        "--min-files",
        type=int,
        default=5,
        help="Minimum pending files to trigger compilation (default: 5)",
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=24,
        help="Maximum hours to wait before forcing compilation (default: 24)",
    )
    parser.add_argument(
        "--check-every",
        type=int,
        default=30,
        help="Check interval in minutes (default: 30)",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run compilation once and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Wiki directories point to Obsidian vault (production data)
    raw_dir = Path("/Users/samcao/Obsidian/wiki/raw")
    wiki_dir = Path("/Users/samcao/Obsidian/wiki/wiki")

    # Callbacks for nice output
    def on_compile_start(count: int):
        print(f"\n🔄 开始编译 {count} 个 Raw 材料...")

    def on_compile_complete(input_count: int, output_count: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"✅ 编译完成 [{now}]")
        print(f"   输入：{input_count} 个 Raw 文件")
        print(f"   输出：{output_count} 个 Wiki 词条")
        print()

    if args.run_once:
        # Run compilation once and exit
        from src.compiler.raw_processor import RawProcessor
        from src.compiler.wiki_builder import WikiBuilder
        from src.compiler.index_generator import IndexGenerator

        processor = RawProcessor(raw_dir)
        builder = WikiBuilder(processor, wiki_dir)
        index_gen = IndexGenerator(wiki_dir)

        pending = processor.list_all(status="raw")
        if not pending:
            print("ℹ️  没有待编译的文件")
            sys.exit(0)

        print(f"🔄 编译 {len(pending)} 个文件...")
        total_created = 0
        for path in pending:
            created = builder.compile(path)
            total_created += len(created)
            print(f"   ✓ {path.name} → {len(created)} 个词条")

        index_gen.generate()
        print(f"\n✅ 完成！生成 {total_created} 个 Wiki 词条")

    else:
        # Start scheduler
        scheduler = create_scheduler(
            raw_dir=raw_dir,
            wiki_dir=wiki_dir,
            config={
                "min_pending_count": args.min_files,
                "max_wait_hours": args.max_wait,
                "check_interval_minutes": args.check_every,
            },
        )

        scheduler.on_compile_start = on_compile_start
        scheduler.on_compile_complete = on_compile_complete

        # Handle shutdown signals
        def signal_handler(sig, frame):
            print("\n\n⏹️  停止自动编译调度器...")
            scheduler.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Print status
        status = scheduler.get_status()
        print("""
╔══════════════════════════════════════════════════════════╗
║        🔄 Agentic Wiki - Auto-Compile Scheduler          ║
╠══════════════════════════════════════════════════════════╣
║  监控 raw/articles/ 目录，自动触发编译                       ║
║                                                          ║
║  触发条件 (满足任一即可):                                 ║
║    1. raw/articles/ 中待编译文件 ≥ {min_files} 个                 ║
║    2. 距离上次编译 ≥ {max_wait} 小时                            ║
║    3. 每天 22:00 强制编译（如果有待处理文件）                  ║
║                                                          ║
║  检查频率：每 {check_every} 分钟                                  ║
║                                                          ║
║  按 Ctrl+C 停止                                           ║
╚══════════════════════════════════════════════════════════╝
""".format(
            min_files=args.min_files,
            max_wait=args.max_wait,
            check_every=args.check_every,
        ))

        print(f"📊 当前状态:")
        print(f"   待编译文件：{status['pending_count']}")
        if status['pending_files']:
            for f in status['pending_files'][:5]:
                print(f"      - {Path(f).name}")
            if len(status['pending_files']) > 5:
                print(f"      ... 还有 {len(status['pending_files']) - 5} 个")
        print(f"   上次编译：{status['last_compile_time'] or '从未'}")
        print()

        # Start scheduler
        scheduler.start()


if __name__ == "__main__":
    main()
