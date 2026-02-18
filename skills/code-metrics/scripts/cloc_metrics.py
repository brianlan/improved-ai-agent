#!/usr/bin/env python3
"""
Run cloc (Count Lines of Code) and parse the output.

Physical size metrics: LOC, SLOC, comment ratio, file count.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def run_cloc(directory: str, exclude: list[str] | None = None) -> Dict[str, Any]:
    """
    Run cloc on a directory and return parsed metrics.

    Args:
        directory: Path to analyze
        exclude: List of directory names to exclude (e.g., ['configs', '__pycache__'])

    Returns:
        Dict with metrics: files, blank, comment, code, comment_ratio
    """
    exclude_args = []
    if exclude:
        for pattern in exclude:
            exclude_args.extend(['--exclude-dir', pattern])

    cmd = ['cloc', '--json', *exclude_args, directory]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            # cloc may return non-zero but still output JSON
            pass

        data = json.loads(result.stdout)

        # Sum across all languages
        total = data.get('SUM', {})
        header = data.get('header', {})

        code = total.get('code', 0)
        comment = total.get('comment', 0)

        return {
            'files': total.get('nFiles', 0),
            'blank': total.get('blank', 0),
            'comment': comment,
            'code': code,
            'comment_ratio': round(comment / code * 100, 1) if code > 0 else 0.0
        }

    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'files': 0,
            'blank': 0,
            'comment': 0,
            'code': 0,
            'comment_ratio': 0.0
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: cloc_metrics.py <directory> [exclude_dir1,exclude_dir2,...]")
        sys.exit(1)

    directory = sys.argv[1]
    exclude = sys.argv[2].split(',') if len(sys.argv) > 2 else None

    result = run_cloc(directory, exclude)

    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Output as JSON for easy parsing
    print(json.dumps(result))


if __name__ == '__main__':
    main()
