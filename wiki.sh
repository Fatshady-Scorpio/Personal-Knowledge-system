#!/bin/bash
# Wiki CLI wrapper - convenient entry point for the Personal Knowledge System
#
# Usage:
#   ./wiki.sh query "What is Transformer?"
#   ./wiki.sh compile [--all | --file path]
#   ./wiki.sh stats
#   ./wiki.sh health
#   ./wiki.sh chat
#   ./wiki.sh help

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$PROJECT_ROOT"

usage() {
    echo "Wiki CLI - Personal Knowledge System (Agentic Wiki)"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  query <question>     Query the wiki knowledge base"
    echo "  compile [--all|--file PATH]"  Compile raw materials into wiki entries
    echo "  stats                Show wiki statistics"
    echo "  health               Run health check"
    echo "  chat                 Start interactive chat mode"
    echo "  help                 Show this help"
    echo ""
}

case "${1:-help}" in
    query)
        shift
        if [ -z "$1" ]; then
            echo "Usage: $0 query <question>"
            exit 1
        fi
        python "$PROJECT_ROOT/scripts/query_wiki.py" "$@"
        ;;
    compile)
        shift
        if [ -z "$1" ]; then
            echo "Usage: $0 compile --all | --file PATH"
            exit 1
        fi
        python "$PROJECT_ROOT/scripts/compile_raw.py" "$@"
        ;;
    stats)
        echo "=== Wiki Statistics ==="
        CONCEPT_COUNT=$(ls "$PROJECT_ROOT/wiki/concepts/"*.md 2>/dev/null | wc -l | tr -d ' ')
        TOPIC_COUNT=$(ls "$PROJECT_ROOT/wiki/topics/"*.md 2>/dev/null | wc -l | tr -d ' ')
        RAW_COUNT=$(ls "$PROJECT_ROOT/raw/articles/"*.md 2>/dev/null | wc -l | tr -d ' ')
        QA_COUNT=$(ls "$PROJECT_ROOT/outputs/qa/"*.md 2>/dev/null | wc -l | tr -d ' ')
        INDEX_EXISTS="no"
        [ -f "$PROJECT_ROOT/wiki/index.md" ] && INDEX_EXISTS="yes"

        echo "  Concept entries: $CONCEPT_COUNT"
        echo "  Topic entries:   $TOPIC_COUNT"
        echo "  Index file:      $INDEX_EXISTS"
        echo "  Pending raw:     $RAW_COUNT"
        echo "  Q&A records:     $QA_COUNT"
        ;;
    health)
        python "$PROJECT_ROOT/scripts/health_check.py" --verbose
        ;;
    chat)
        python "$PROJECT_ROOT/scripts/chat.py" "$@"
        ;;
    help|*)
        usage
        ;;
esac
