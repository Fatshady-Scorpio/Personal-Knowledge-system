#!/usr/bin/env python3
"""Setup script for Personal Knowledge Base."""

import os
import sys
from pathlib import Path


def setup_directories():
    """Create the knowledge base directory structure."""
    root = Path(__file__).parent.parent
    knowledge_root = root / "knowledge"

    directories = [
        "00-Inbox",
        "10-Raw/articles",
        "10-Raw/videos",
        "10-Raw/papers",
        "20-Processed/summaries",
        "20-Processed/notes",
        "30-Topics/AI",
        "30-Topics/Investment",
        "30-Topics/Gaming",
        "40-Maps",
        "50-Outputs",
        "90-Archive",
    ]

    for dir_name in directories:
        dir_path = knowledge_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")

    # Create .gitkeep files
    for dir_path in knowledge_root.rglob("*"):
        if dir_path.is_dir():
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    print("\n✓ Knowledge base directory structure created!")


def check_env():
    """Check if environment variables are configured."""
    env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        print("\n⚠ Warning: .env file not found!")
        print("Please copy .env.example to .env and configure your API key:")
        print("  cp .env.example .env")
        return False

    # Check for API key
    with open(env_file, "r") as f:
        content = f.read()

    if "BAILOU_API_KEY=" not in content or "sk-your-api-key-here" in content:
        print("\n⚠ Warning: BAILOU_API_KEY not configured in .env!")
        print("Please edit .env and set your Alibaba Cloud Bailian API key.")
        return False

    print("\n✓ Environment configuration OK")
    return True


def main():
    """Run setup."""
    print("=" * 50)
    print("Personal Knowledge Base - Setup")
    print("=" * 50)

    setup_directories()
    check_env()

    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
