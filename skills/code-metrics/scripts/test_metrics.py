#!/usr/bin/env python3
"""
Run pytest and coverage to get test metrics.
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def run_pytest_collect(directory: str) -> Dict[str, Any]:
    """Collect test cases using pytest --collect-only."""
    cmd = ['pytest', directory, '--collect-only', '-q']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout

        # Parse pytest collection output
        # Format: X test case Y collected in Z.ZZs
        match = re.search(r'(\d+)\s+test(?:s)?\s+collected', output)
        test_count = int(match.group(1)) if match else 0

        # Also try to count lines that look like test items
        # Lines typically start with "  <Module " or "    <Function "
        lines = output.split('\n')
        modules = len([l for l in lines if '<Module' in l])
        classes = len([l for l in lines if '<Class' in l])

        return {
            'test_count': test_count,
            'test_modules': modules,
            'test_classes': classes
        }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'test_count': 0,
            'test_modules': 0,
            'test_classes': 0
        }


def run_coverage(directory: str, source_dirs: list[str] | None = None) -> Dict[str, Any]:
    """
    Run coverage and return coverage metrics.

    Args:
        directory: Test directory to run
        source_dirs: Source directories to measure coverage for
    """
    # Build coverage command
    cmd = ['coverage', 'run', '-m', 'pytest', directory, '-q']

    try:
        # First run coverage (only if no existing coverage data or --run-coverage flag)
        # Check if we should skip the run
        import sys
        skip_run = '--skip-run' in sys.argv

        if not skip_run:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

        # Then get report
        # Use "coverage json" command (coverage.py 7.x) which writes to coverage.json file
        report_cmd = ['coverage', 'json', '--ignore-errors', '-o', '/tmp/coverage_metrics.json']
        subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Parse coverage JSON output from file
        try:
            with open('/tmp/coverage_metrics.json', 'r') as f:
                data = json.load(f)
            files = data.get('files', {})

            # Calculate totals
            total_statements = sum(f.get('summary', {}).get('num_statements', 0) for f in files.values())
            total_missing = sum(f.get('summary', {}).get('missing_lines', 0) for f in files.values())
            total_covered = total_statements - total_missing

            # Filter by source directories if specified
            if source_dirs:
                filtered_files = {}
                for filepath, metrics in files.items():
                    # File paths in coverage.json are relative to project root
                    # Check if filepath starts with any of the source directory names
                    for d in source_dirs:
                        dir_name = Path(d).name  # Get just the directory name (e.g., "prefusion")
                        if filepath.startswith(dir_name + '/'):
                            filtered_files[filepath] = metrics
                            break

                if filtered_files:
                    total_statements = sum(f.get('summary', {}).get('num_statements', 0) for f in filtered_files.values())
                    total_missing = sum(f.get('summary', {}).get('missing_lines', 0) for f in filtered_files.values())
                    total_covered = total_statements - total_missing
                    files = filtered_files
                else:
                    # No files matched the filter
                    return {
                        'statement_coverage': 0,
                        'statements': 0,
                        'covered': 0,
                        'missing': 0,
                        'files_measured': 0,
                        'filtered': True
                    }

            coverage_pct = round(total_covered / total_statements * 100, 1) if total_statements > 0 else 0

            return {
                'statement_coverage': coverage_pct,
                'statements': total_statements,
                'covered': total_covered,
                'missing': total_missing,
                'files_measured': len(files)
            }

        except json.JSONDecodeError:
            # Fallback to parsing text output
            report_text_cmd = ['coverage', 'report']
            text_result = subprocess.run(
                report_text_cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # Parse last line for totals
            # Format: TOTAL    XXXX    YYY    ZZ%
            for line in reversed(text_result.stdout.split('\n')):
                if 'TOTAL' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            coverage_pct = float(parts[-1].rstrip('%'))
                            return {
                                'statement_coverage': coverage_pct,
                                'files_measured': 0,
                                'statements': 0,
                                'covered': 0,
                                'missing': 0
                            }
                        except ValueError:
                            pass

            return {
                'statement_coverage': 0,
                'files_measured': 0,
                'statements': 0,
                'covered': 0,
                'missing': 0
            }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'statement_coverage': 0,
            'files_measured': 0,
            'statements': 0,
            'covered': 0,
            'missing': 0
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: test_metrics.py <test_directory> [source_dir1,source_dir2,...]")
        sys.exit(1)

    directory = sys.argv[1]
    source_dirs = sys.argv[2].split(',') if len(sys.argv) > 2 else None

    result = {
        'pytest': run_pytest_collect(directory),
    }

    # Only run coverage if explicitly requested (takes time)
    if '--coverage' in sys.argv:
        result['coverage'] = run_coverage(directory, source_dirs)

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
