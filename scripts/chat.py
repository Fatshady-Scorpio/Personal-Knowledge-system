#!/usr/bin/env python3
"""Interactive Chat - Chat with your wiki knowledge base.

This provides a convenient chat interface for querying your knowledge base.

Usage:
    PYTHONPATH=. python scripts/chat.py [options]

Options:
    --model MODEL     Model to use (default: qwen3.6-plus)
    --budget TOKENS   Token budget (default: 100000)
    --verbose         Show detailed output
"""

import argparse
import logging
from pathlib import Path
from datetime import datetime

from src.query.agent_query import AgentQuery
from src.query.context_manager import ContextManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Chat with your wiki knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/chat.py
    python scripts/chat.py --model qwen3.6-plus --budget 150000
    python scripts/chat.py --verbose
        """,
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.6-plus",
        help="Model to use (default: qwen3.6-plus)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=100000,
        help="Token budget (default: 100000)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save Q&A results",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get project root
    root_dir = Path(__file__).parent.parent
    wiki_dir = root_dir / "wiki"
    outputs_dir = root_dir / "outputs" / "qa"

    # Initialize query engine
    agent = AgentQuery(
        wiki_dir=wiki_dir,
        outputs_dir=outputs_dir,
        model=args.model,
        token_budget=args.budget,
    )

    # Print header
    print_header()

    # Show stats
    show_stats(wiki_dir)

    # Main chat loop
    run_chat_loop(agent, save=not args.no_save)


def print_header():
    """Print chat header."""
    print("""
╔══════════════════════════════════════════════════════════╗
║             🤖 Agentic Wiki - Chat Mode                  ║
║                                                          ║
║  你的个人知识库助手，基于 Karpathy 的 Agentic Wiki 架构        ║
║                                                          ║
║  输入 'help' 查看帮助，'quit' 退出                        ║
╚══════════════════════════════════════════════════════════╝
""")


def show_stats(wiki_dir: Path):
    """Show wiki statistics."""
    concepts = list((wiki_dir / "concepts").glob("*.md")) if (wiki_dir / "concepts").exists() else []
    topics = list((wiki_dir / "topics").glob("*.md")) if (wiki_dir / "topics").exists() else []
    index_exists = (wiki_dir / "index.md").exists()

    print(f"📊 知识库状态:")
    print(f"   概念词条：{len(concepts)}")
    print(f"   主题词条：{len(topics)}")
    print(f"   索引文件：{'✓ 存在' if index_exists else '✗ 不存在'}")
    print()


def run_chat_loop(agent: AgentQuery, save: bool = True):
    """Run the main chat loop.

    Args:
        agent: AgentQuery instance
        save: Whether to save Q&A results
    """
    print("💬 请问吧！\n")

    while True:
        try:
            # Get user input
            user_input = input("❓ 你：").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 再见！")
                break

            if user_input.lower() == "help":
                print_help()
                continue

            if user_input.lower() == "stats":
                show_stats(agent.wiki_dir)
                continue

            if user_input.lower() == "history":
                show_history(agent.outputs_dir)
                continue

            # Process query
            print("\n🔄 思考中...\n")

            answer = agent.query(user_input, save_result=save)

            print(f"💡 助手：\n{answer}\n")
            print("─" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ 错误：{e}\n")


def print_help():
    """Print help message."""
    print("""
可用命令:
  help          显示此帮助消息
  stats         显示知识库统计
  history       显示最近的问答历史
  quit/exit/q   退出聊天

使用技巧:
  1. 问题要具体明确，例如"什么是 Transformer？"
  2. 可以进行连续追问，系统会记住上下文
  3. 使用 [[词条名]] 格式可以引用特定概念
  4. 复杂主题可以拆分成多个问题逐一询问

示例问题:
  - "Agentic Wiki 的核心理念是什么？"
  - "LLM 推理优化有哪些技术？"
  - "RAG 和 Wiki 方式的区别？"
""")


def show_history(outputs_dir: Path, limit: int = 10):
    """Show recent Q&A history.

    Args:
        outputs_dir: Path to outputs/qa directory
        limit: Maximum number of entries to show
    """
    if not outputs_dir.exists():
        print("暂无问答历史")
        return

    qa_files = sorted(outputs_dir.glob("*.md"), reverse=True)[:limit]

    if not qa_files:
        print("暂无问答历史")
        return

    print("\n最近的问答历史:\n")
    for i, f in enumerate(qa_files, 1):
        # Extract question from filename
        parts = f.stem.split("_", 2)
        if len(parts) >= 3:
            question = parts[2].replace("_", " ")
        else:
            question = f.stem

        # Get file time
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        time_str = mtime.strftime("%Y-%m-%d %H:%M")

        print(f"  {i}. [{time_str}] {question[:50]}...")

    print()


if __name__ == "__main__":
    main()
