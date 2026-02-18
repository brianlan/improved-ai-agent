#!/usr/bin/env python3
"""
Run ruff to get lint statistics and code quality warnings.
"""
import json
import subprocess
import sys
from typing import Dict, Any, List


def run_ruff(directory: str) -> Dict[str, Any]:
    """Run ruff check and return statistics."""
    # Get JSON output for detailed parsing
    cmd = ['ruff', 'check', directory, '--output-format=json', '--statistics']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Parse JSON output
        try:
            violations = json.loads(result.stdout) if result.stdout else []
        except json.JSONDecodeError:
            violations = []

        # Count by error code
        error_counts: Dict[str, int] = {}
        file_counts: Dict[str, int] = {}

        for v in violations:
            code = v.get('code', 'UNKNOWN')
            filename = v.get('filename', 'unknown')

            error_counts[code] = error_counts.get(code, 0) + 1
            file_counts[filename] = file_counts.get(filename, 0) + 1

        # Get summary stats
        summary_cmd = ['ruff', 'check', directory, '--statistics']
        summary_result = subprocess.run(
            summary_cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Try to extract total from summary output
        total_violations = len(violations)

        # Get top error codes
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get files with most violations
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_violations': total_violations,
            'files_with_issues': len(file_counts),
            'unique_error_codes': len(error_counts),
            'top_errors': top_errors,
            'top_files': [(Path(f).name, c) for f, c in top_files]
        }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'total_violations': 0,
            'files_with_issues': 0,
            'unique_error_codes': 0
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: ruff_metrics.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    result = run_ruff(directory)

    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
