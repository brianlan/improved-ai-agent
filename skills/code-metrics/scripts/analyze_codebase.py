#!/usr/bin/env python3
"""
Main aggregator script for code metrics analysis.

Runs all tools (cloc, radon, ruff, pytest, coverage) and produces a formatted report.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


def run_cloc(directory: str, exclude: List[str] | None = None) -> Dict[str, Any]:
    """Run cloc_metrics.py script."""
    exclude_arg = ','.join(exclude) if exclude else ''
    cmd = [sys.executable, str(SCRIPT_DIR / 'cloc_metrics.py'), directory, exclude_arg]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {'error': result.stderr}
    return json.loads(result.stdout)


def run_radon(directory: str, threshold: str = 'B') -> Dict[str, Any]:
    """Run radon_metrics.py script."""
    cmd = [sys.executable, str(SCRIPT_DIR / 'radon_metrics.py'), directory, threshold]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {'error': result.stderr}
    return json.loads(result.stdout)


def run_ruff(directory: str) -> Dict[str, Any]:
    """Run ruff_metrics.py script."""
    cmd = [sys.executable, str(SCRIPT_DIR / 'ruff_metrics.py'), directory]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {'error': result.stderr}
    return json.loads(result.stdout)


def run_test_metrics(
    directory: str,
    coverage: bool = False,
    source_dirs: List[str] | None = None,
    skip_run: bool = False
) -> Dict[str, Any]:
    """Run test_metrics.py script."""
    args = [sys.executable, str(SCRIPT_DIR / 'test_metrics.py'), directory]
    # source_dirs must come before --coverage flag
    if source_dirs:
        args.append(','.join(source_dirs))
    if coverage:
        args.append('--coverage')
    if skip_run:
        args.append('--skip-run')

    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {'error': result.stderr}
    return json.loads(result.stdout)


def analyze_directory(
    directory: str,
    name: str,
    exclude: List[str] | None = None,
    is_tests: bool = False,
    run_coverage: bool = False
) -> Dict[str, Any]:
    """
    Analyze a single directory with all tools.

    Args:
        directory: Path to analyze
        name: Display name for the directory
        exclude: Directories to exclude
        is_tests: Whether this is the tests directory (affects thresholds)
        run_coverage: Whether to run coverage analysis

    Returns:
        Dict with all metrics for the directory
    """
    # Use stricter threshold for source code, looser for tests
    cc_threshold = 'D' if is_tests else 'B'

    result = {
        'name': name,
        'path': directory,
        'exists': Path(directory).exists(),
    }

    if not result['exists']:
        result['error'] = f'Directory not found: {directory}'
        return result

    # Run all metric collectors
    result['cloc'] = run_cloc(directory, exclude)
    result['radon'] = run_radon(directory, cc_threshold)
    result['ruff'] = run_ruff(directory)

    # Only run pytest for tests directory or if explicitly requested
    if is_tests or 'test' in directory.lower():
        result['tests'] = run_test_metrics(directory, run_coverage)

    return result


def format_report(results: List[Dict[str, Any]], show_coverage: bool = False) -> str:
    """Format metrics as a readable report."""
    lines = []
    lines.append('=' * 80)
    lines.append('CODEBASE METRICS REPORT')
    lines.append('=' * 80)
    lines.append('')

    # Summary table header
    lines.append('┌──────────────────┬────────┬────────┬──────────┬────────┬─────────┬──────────┐')
    lines.append('│ Directory        │  Files │  SLOC  │ Cls/Mtd │ Max CC │ Low MI  │ Coverage│')
    lines.append('├──────────────────┼────────┼────────┼──────────┼────────┼─────────┼──────────┤')

    for r in results:
        if not r.get('exists'):
            lines.append(f'│ {r["name"]:16} │ NOT FOUND │')
            continue

        cloc = r.get('cloc', {})
        radon = r.get('radon', {})
        tests = r.get('tests', {})

        files = cloc.get('files', 0)
        sloc = cloc.get('code', 0)
        raw = radon.get('raw', {})
        classes = raw.get('classes', 0)
        methods = raw.get('methods', 0)
        functions = raw.get('functions', 0)
        # Format: C/M/F (Classes/Methods/Functions)
        cls_mtd = f'{classes}/{methods}/{functions}' if classes or methods or functions else '0/0/0'
        max_cc = radon.get('cc', {}).get('max_cc', 0)
        low_mi = radon.get('mi', {}).get('low_maintainability', 0)
        coverage = tests.get('coverage', {}).get('statement_coverage', 0) if show_coverage else 'N/A'

        lines.append(f'│ {r["name"]:16} │ {files:6} │ {sloc:6} │ {cls_mtd:8} │ {max_cc:6} │ {low_mi:7} │ {str(coverage):>8}│')

    lines.append('└──────────────────┴────────┴────────┴──────────┴────────┴─────────┴──────────┘')
    lines.append('')

    # Detailed breakdown per directory
    for r in results:
        if not r.get('exists'):
            continue

        lines.append('-' * 80)
        lines.append(f'## {r["name"]} ({r["path"]})')
        lines.append('')

        # Physical size
        cloc = r.get('cloc', {})
        lines.append('### Physical Size (cloc)')
        lines.append(f"  Files:       {cloc.get('files', 0)}")
        lines.append(f"  SLOC:        {cloc.get('code', 0)}")
        lines.append(f"  Comments:    {cloc.get('comment', 0)} ({cloc.get('comment_ratio', 0)}%)")
        lines.append('')

        # Logical size & complexity
        radon = r.get('radon', {})
        raw = radon.get('raw', {})
        cc = radon.get('cc', {})
        mi = radon.get('mi', {})

        lines.append('### Logical Size & Complexity (radon)')
        lines.append(f"  Classes:     {raw.get('classes', 0)}")
        lines.append(f"  Methods:     {raw.get('methods', 0)}")
        lines.append(f"  Functions:   {raw.get('functions', 0)}")
        lines.append(f"  Total callable units: {raw.get('total_callable_units', 0)}")
        lines.append(f"  Avg func len: {raw.get('avg_function_length', 0)} LOC")
        lines.append('')
        lines.append(f"  Max CC:      {cc.get('max_cc', 0)}")
        # Show location of max CC if available
        max_cc_loc = cc.get('max_cc_location', {})
        if max_cc_loc and max_cc_loc.get('file'):
            # Extract filename from full path for readability
            file_path = max_cc_loc['file']
            filename = file_path.split('/')[-1] if '/' in file_path else file_path
            lines.append(f"    Location: {filename} ({max_cc_loc.get('rank', 'N/A')})")
        lines.append(f"  High risk:   {cc.get('high_risk_count', 0)} functions (C or worse)")
        cc_dist = cc.get('cc_counts', {})
        lines.append(f"  CC dist:     A:{cc_dist.get('A', 0)} B:{cc_dist.get('B', 0)} C:{cc_dist.get('C', 0)} D:{cc_dist.get('D', 0)} E:{cc_dist.get('E', 0)} F:{cc_dist.get('F', 0)}")
        lines.append('')
        lines.append(f"  Avg MI:      {mi.get('avg_mi', 0)}")
        lines.append(f"  Low MI:      {mi.get('low_maintainability', 0)} files (C/D/F)")
        lines.append('')

        # Lint warnings
        ruff = r.get('ruff', {})
        lines.append('### Code Quality (ruff)')
        lines.append(f"  Warnings:    {ruff.get('total_violations', 0)}")
        lines.append(f"  Files with issues: {ruff.get('files_with_issues', 0)}")
        top_errors = ruff.get('top_errors', [])[:3]
        if top_errors:
            lines.append(f"  Top errors:  {', '.join(f'{k}({v})' for k, v in top_errors)}")
        lines.append('')

        # Test metrics
        if 'tests' in r:
            tests = r.get('tests', {})
            pytest_info = tests.get('pytest', {})
            lines.append('### Test Metrics (pytest)')
            lines.append(f"  Test cases:  {pytest_info.get('test_count', 0)}")
            lines.append(f"  Test modules: {pytest_info.get('test_modules', 0)}")
            if 'coverage' in tests:
                cov = tests.get('coverage', {})
                lines.append('')
                lines.append('### Coverage')
                lines.append(f"  Statement coverage: {cov.get('statement_coverage', 0)}%")
                lines.append(f"  Files measured: {cov.get('files_measured', 0)}")
            lines.append('')

    lines.append('=' * 80)
    lines.append('')
    lines.append('INTERPRETATION GUIDE:')
    lines.append('  SLOC:      Source Lines of Code (physical size)')
    lines.append('  Max CC:    Maximum cyclomatic complexity (lower is better, <10 is good)')
    lines.append('  Low MI:    Files with low maintainability index (lower is worse)')
    lines.append('  Coverage:  Test coverage percentage (higher is better, >80% is good)')
    lines.append('')
    lines.append('CC Ranks: A(1-5) B(6-10) C(11-20) D(21-30) E(31-40) F(41+)')
    lines.append('MI Ranks: A(100-20) B(19-10) C(9-0) D(<0) F(unranked)')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze Python codebase metrics')
    parser.add_argument('directories', nargs='*', help='Directories to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze all main directories (prefusion, tools, contrib, tests)')
    parser.add_argument('--exclude', default='configs,__pycache__,.git,build,dist', help='Comma-separated dirs to exclude')
    parser.add_argument('--coverage', action='store_true', help='Run coverage analysis (slow)')
    parser.add_argument('--json', action='store_true', help='Output as JSON instead of formatted report')
    parser.add_argument('--project-root', default='.', help='Root directory of the project')

    args = parser.parse_args()

    # Determine which directories to analyze
    exclude_dirs = args.exclude.split(',')
    directories = []

    if args.all:
        root = Path(args.project_root)
        directories = [
            ('prefusion', str(root / 'prefusion')),
            ('tools', str(root / 'tools')),
            ('contrib', str(root / 'contrib')),
            ('tests', str(root / 'tests')),
        ]
    elif args.directories:
        for d in args.directories:
            path = Path(d)
            directories.append((path.name, str(path)))
    else:
        # Default to current directory
        directories = [('current', '.')]

    # Run coverage once before analyzing directories
    # Coverage runs tests from tests directory and measures coverage of source code
    coverage_results = {}
    tests_dir = None

    if args.coverage:
        # Find tests directory and source directories
        source_dirs = []
        for name, path in directories:
            if 'test' in name.lower():
                tests_dir = path
            else:
                source_dirs.append((name, path))

        if tests_dir and source_dirs:
            # Run coverage once for the first source directory (which runs pytest)
            # Then use --skip-run for subsequent directories to avoid re-running tests
            for i, (name, path) in enumerate(source_dirs):
                if i == 0:
                    # First run - executes pytest
                    cov_result = run_test_metrics(tests_dir, coverage=True, source_dirs=[path], skip_run=False)
                else:
                    # Subsequent runs - use --skip-run flag
                    cov_result = run_test_metrics(tests_dir, coverage=True, source_dirs=[path], skip_run=True)

                if 'coverage' in cov_result:
                    coverage_results[name] = cov_result['coverage']

    # Run analysis
    results = []
    for name, path in directories:
        is_tests = 'test' in name.lower()
        result = analyze_directory(
            path,
            name,
            exclude=exclude_dirs,
            is_tests=is_tests,
            run_coverage=False  # Don't run coverage per-directory
        )

        # Apply coverage results for non-test directories
        if not is_tests and args.coverage and name in coverage_results:
            result['tests'] = {'coverage': coverage_results[name]}

        results.append(result)

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_report(results, show_coverage=args.coverage))


if __name__ == '__main__':
    main()
