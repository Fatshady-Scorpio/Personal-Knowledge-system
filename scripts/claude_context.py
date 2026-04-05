#!/usr/bin/env python3
"""Load knowledge context for Claude sessions.

Usage:
    # Get context for a topic
    python scripts/claude_context.py "机器学习"

    # Load saved context for session
    python scripts/claude_context.py --load --session my_session

    # Save context for later
    python scripts/claude_context.py "深度学习" --save --session dl_session
"""

import argparse
from src.agent.context_injector import ContextInjector


def main():
    parser = argparse.ArgumentParser(description="Claude context loader")
    parser.add_argument("query", nargs="?", help="Query to get context for")
    parser.add_argument("--load", action="store_true", help="Load saved context")
    parser.add_argument("--save", action="store_true", help="Save context")
    parser.add_argument("--session", default="default", help="Session ID")
    parser.add_argument("--full", action="store_true", help="Include full content")
    args = parser.parse_args()

    injector = ContextInjector()

    if args.load:
        context = injector.load_context(args.session)
        if context:
            print(context)
        else:
            print(f"No saved context found for session: {args.session}")
    elif args.query:
        context = injector.get_context(args.query, max_notes=5, include_full_content=args.full)
        print(context)

        if args.save:
            path = injector.save_context(args.query, context, args.session)
            print(f"\nContext saved to: {path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
