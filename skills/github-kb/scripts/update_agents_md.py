#!/usr/bin/env python3
"""
Helper script to update AGENTS.md with a new repository entry.

Usage:
    python update_agents_md.py <repo-owner> <repo-name> <summary>

Example:
    python update_agents_md.py facebook react "A JavaScript library for building user interfaces"
"""

import sys
import os
from pathlib import Path


def update_agents_md(
    repo_owner: str,
    repo_name: str,
    summary: str,
    kb_path: str = "/ssd4/github-knowledge-base",
):
    """
    Update AGENTS.md with a new repository entry.

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        summary: One-sentence summary of the repository
        kb_path: Path to the knowledge base directory
    """
    agents_md_path = Path(kb_path) / "AGENTS.md"

    # Ensure AGENTS.md exists
    if not agents_md_path.exists():
        print(f"Error: AGENTS.md not found at {agents_md_path}")
        sys.exit(1)

    # Read current content
    with open(agents_md_path, "r") as f:
        content = f.read()

    # Create the new entry
    full_repo_name = f"{repo_owner}/{repo_name}"
    entry = f"\n### [{full_repo_name}]({repo_name})\n\n{summary}\n"

    # Check if entry already exists
    if f"[{full_repo_name}]" in content:
        print(f"Repository {full_repo_name} already exists in AGENTS.md")
        return

    # Append the new entry
    with open(agents_md_path, "a") as f:
        f.write(entry)

    print(f"✅ Added {full_repo_name} to AGENTS.md")


def main():
    if len(sys.argv) < 4:
        print("Usage: python update_agents_md.py <repo-owner> <repo-name> <summary>")
        print("\nExample:")
        print(
            '    python update_agents_md.py facebook react "A JavaScript library for building user interfaces"'
        )
        sys.exit(1)

    repo_owner = sys.argv[1]
    repo_name = sys.argv[2]
    summary = sys.argv[3]

    update_agents_md(repo_owner, repo_name, summary)


if __name__ == "__main__":
    main()
