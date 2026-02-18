#!/usr/bin/env python3
"""
Run radon for Python code metrics: logical size, cyclomatic complexity, and maintainability index.
"""
import json
import re
import subprocess
import sys
from typing import Dict, Any, List


def run_radon_raw(directory: str) -> Dict[str, Any]:
    """
    Get logical size metrics by parsing radon cc output.

    Radon cc output prefixes:
    - C: Classes
    - M: Methods (functions inside classes)
    - F: Functions (module-level standalone functions)

    Note: Named 'raw' for backwards compatibility with the skill's API.
    """
    cmd = ['radon', 'cc', directory, '-a', '-s']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout

        classes = 0
        methods = 0
        functions = 0

        for line in output.split('\n'):
            parts = line.strip().split()
            if len(parts) >= 2:
                prefix = parts[0]
                if prefix == 'C':
                    classes += 1
                elif prefix == 'M':
                    methods += 1
                elif prefix == 'F':
                    functions += 1

        # Total callable units = standalone functions + methods
        total_callable_units = functions + methods

        # Calculate LLOC using radon raw (for avg function length)
        lloc_cmd = ['radon', 'raw', directory, '-j']
        total_lloc = 0
        try:
            lloc_result = subprocess.run(lloc_cmd, capture_output=True, text=True, check=False)
            if lloc_result.returncode == 0:
                import json
                data = json.loads(lloc_result.stdout)
                total_lloc = sum(f.get('lloc', 0) for f in data.values())
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        avg_function_length = round(total_lloc / total_callable_units, 1) if total_callable_units > 0 else 0

        return {
            'classes': classes,
            'methods': methods,
            'functions': functions,
            'total_callable_units': total_callable_units,
            'lloc': total_lloc,
            'avg_function_length': avg_function_length
        }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'classes': 0,
            'methods': 0,
            'functions': 0,
            'total_callable_units': 0,
            'lloc': 0,
            'avg_function_length': 0
        }


def run_radon_cc(directory: str, threshold: str = 'B') -> Dict[str, Any]:
    """
    Get cyclomatic complexity metrics.

    Thresholds: A (1-5), B (6-10), C (11-20), D (21-30), E (31-40), F (41+)
    """
    # First get all complexities
    cmd_all = ['radon', 'cc', directory, '-a', '-s']

    try:
        result = subprocess.run(
            cmd_all,
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout

        # Parse complexity output
        # Format:
        #   /path/to/file.py
        #       F 14:0 calculate_bbox3d_ap - E (37)
        #       M 123:4 some_method - B (7)
        #       C 10:0 ClassName - A (4)
        max_cc = 0
        max_cc_location = {}  # Track location of max CC
        cc_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
        high_risk = []
        current_file = None  # Track current file being parsed

        for line in output.split('\n'):
            # Check if line is a file path (starts with / and has .py, no leading whitespace)
            if line.strip().startswith('/') and '.py' in line and not line[0].isspace():
                current_file = line.strip()
                continue

            # Match patterns like: F 14:0 func_name - RANK (complexity)
            cc_match = re.search(r'\((\d+)\)(\s*\([A-F]\))?', line)
            if cc_match:
                cc = int(cc_match.group(1))
                # Rank is the letter between '-' and '(' like: - E (37)
                rank_match = re.search(r'-\s+([A-F])\s+\(', line)
                rank = rank_match.group(1) if rank_match else 'A'

                # Track max CC location
                if cc > max_cc:
                    max_cc = cc
                    # Extract line number and name from the line
                    # Format: F 14:0 func_name - RANK (cc)
                    # or M 123:4 method_name - RANK (cc)
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        # parts[0] = F/M/C, parts[1] = line:col, parts[2] = name
                        line_col = parts[1]
                        name = parts[2]

                        if current_file:
                            # Extract just the filename from the full path
                            filename = current_file.split('/')[-1]
                            location = f"{filename}:{line_col}:{name}"
                        else:
                            location = f"{line_col}:{name}"

                        max_cc_location = {
                            'file': location,
                            'full_path': current_file,
                            'complexity': cc,
                            'rank': rank
                        }

                if rank in cc_counts:
                    cc_counts[rank] += 1

                # Track high-risk functions (C or worse)
                if rank in ['C', 'D', 'E', 'F']:
                    # Extract function name
                    func_match = re.search(r'(\w+)\s+\(', line)
                    if func_match:
                        high_risk.append({
                            'function': func_match.group(1),
                            'complexity': cc,
                            'rank': rank
                        })

        # Now get filtered output for threshold
        cmd_filter = ['radon', 'cc', directory, f'-n{threshold}', '-s']
        result_filter = subprocess.run(
            cmd_filter,
            capture_output=True,
            text=True,
            check=False
        )

        above_threshold = len([l for l in result_filter.stdout.split('\n') if l.strip()])

        return {
            'max_cc': max_cc,
            'max_cc_location': max_cc_location,
            'cc_counts': cc_counts,
            'above_threshold': above_threshold,
            'high_risk_count': sum(cc_counts[r] for r in ['C', 'D', 'E', 'F']),
            'high_risk_sample': high_risk[:5]  # Top 5 high-risk functions
        }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'max_cc': 0,
            'max_cc_location': {},
            'cc_counts': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0},
            'above_threshold': 0,
            'high_risk_count': 0
        }


def run_radon_mi(directory: str) -> Dict[str, Any]:
    """Get Maintainability Index scores."""
    cmd = ['radon', 'mi', directory, '-s']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout

        # Parse MI output
        # Format: FILE - X (X)
        mi_scores = []
        mi_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}

        for line in output.split('\n'):
            # Match: filename - MI (Grade)
            match = re.search(r'(\S+)\s+-\s+([\d.]+)\s+\(([A-F])\)', line)
            if match:
                filename, mi, grade = match.groups()
                mi_scores.append({
                    'file': filename,
                    'mi': float(mi),
                    'grade': grade
                })
                mi_counts[grade] += 1

        # Calculate average MI
        avg_mi = round(sum(s['mi'] for s in mi_scores) / len(mi_scores), 1) if mi_scores else 0

        return {
            'avg_mi': avg_mi,
            'mi_counts': mi_counts,
            'low_maintainability': sum(mi_counts[g] for g in ['C', 'D', 'F']),
            'files_analyzed': len(mi_scores)
        }

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return {
            'error': str(e),
            'avg_mi': 0,
            'mi_counts': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
            'low_maintainability': 0
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: radon_metrics.py <directory> [threshold]")
        print("Threshold options: A, B, C, D (default: B)")
        sys.exit(1)

    directory = sys.argv[1]
    threshold = sys.argv[2] if len(sys.argv) > 2 else 'B'

    result = {
        'raw': run_radon_raw(directory),
        'cc': run_radon_cc(directory, threshold),
        'mi': run_radon_mi(directory)
    }

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
