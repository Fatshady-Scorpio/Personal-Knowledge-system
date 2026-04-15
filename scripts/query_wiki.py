#!/usr/bin/env python3
"""Query the wiki knowledge base.

Usage:
    PYTHONPATH=. python scripts/query_wiki.py "Your question here"

Options:
    --no-save       Don't save the Q&A result
    --interactive   Start interactive Q&A session
    --verbose       Show detailed output
"""

import argparse
import logging
from pathlib import Path

from src.query.agent_query import AgentQuery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Query the wiki knowledge base")
    parser.add_argument("question", nargs="?", type=str, help="Your question")
    parser.add_argument("--no-save", action="store_true", help="Don't save Q&A")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get project root
    root_dir = Path(__file__).parent.parent
    wiki_dir = root_dir / "wiki"
    outputs_dir = root_dir / "outputs" / "qa"

    # Initialize query engine
    agent = AgentQuery(wiki_dir=wiki_dir, outputs_dir=outputs_dir)

    if args.interactive:
        print("🤖 Agentic Wiki - Interactive Query Mode")
        print("Type 'quit' or 'exit' to stop\n")

        while True:
            try:
                question = input("\n❓ 请问：").strip()
                if question.lower() in ["quit", "exit", "q"]:
                    print("再见！")
                    break
                if not question:
                    continue

                print("\n🔄 正在思考...\n")
                answer = agent.query(question, save_result=not args.no_save)
                print(f"\n💡 回答:\n{answer}\n")

            except KeyboardInterrupt:
                print("\n再见！")
                break
            except Exception as e:
                logger.error(f"Error: {e}")

    elif args.question:
        print(f"\n🔄 查询：{args.question}\n")
        answer = agent.query(args.question, save_result=not args.no_save)
        print(f"\n💡 回答:\n{answer}\n")

    else:
        parser.print_help()
        print("\n示例:")
        print('  python scripts/query_wiki.py "什么是 Transformer？"')
        print("  python scripts/query_wiki.py --interactive")


if __name__ == "__main__":
    main()
