#!/usr/bin/env python3
"""Run health check on the wiki knowledge base.

Usage:
    PYTHONPATH=. python scripts/health_check.py [options]

Options:
    --output PATH   Save report to specific path
    --verbose       Show detailed output
"""

import argparse
import logging
from pathlib import Path

from src.maintenance.health_checker import HealthChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run health check on wiki")
    parser.add_argument("--output", type=str, help="Save report to path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get project root
    root_dir = Path(__file__).parent.parent
    wiki_dir = root_dir / "wiki"

    # Initialize health checker
    checker = HealthChecker(wiki_dir)

    # Run checks and generate report
    logger.info("Running health check...")
    results = checker.run_full_check()

    # Generate and display report
    report = checker.generate_report(results)
    print("\n" + report)

    # Save if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info(f"Report saved to: {output_path}")

    # Summary
    stats = results["statistics"]
    print("\n📊 摘要:")
    print(f"  词条总数：{stats['total_entries']}")
    print(f"  断裂链接：{len(results['broken_links'])}")
    print(f"  孤岛词条：{len(results['orphaned_entries'])}")
    print(f"  潜在矛盾：{len(results['contradictions'])}")
    print(f"  缺少来源：{len(results['missing_sources'])}")


if __name__ == "__main__":
    main()
