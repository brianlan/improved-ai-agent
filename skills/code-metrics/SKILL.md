---
name: code-metrics
description: "Calculate comprehensive codebase statistics and metrics for Python projects. Use when analyzing code quality, tracking technical debt, comparing directories, or generating metrics reports. Supports physical size (LOC/SLOC), logical size (functions/classes), cyclomatic complexity, maintainability index, lint warnings, and test coverage. Excludes configs directory by default. Use for generating metrics reports, comparing directories (prefusion/tools/contrib/tests), analyzing all directories with --all, or including test coverage with --coverage."
---

# Code Metrics

## Overview

Analyze Python codebase directories to generate comprehensive metrics including physical size, complexity, maintainability, and test coverage. Uses industry-standard tools (cloc, radon, ruff, pytest, coverage) to produce actionable insights.

## Quick Start

### Analyze All Main Directories

```bash
cd /path/to/project
python3 ~/.claude/skills/code-metrics/scripts/analyze_codebase.py --all
```

Output includes summary table followed by detailed breakdowns:

```
┌──────────────────┬────────┬────────┬──────────┬────────┬─────────┬──────────┐
│ Directory        │  Files │  SLOC  │ Cls/Mtd │ Max CC │ Low MI  │ Coverage│
├──────────────────┼────────┼────────┼──────────┼────────┼─────────┼──────────┤
│ prefusion        │     42 │   3200 │  25/112/85│     18 │       3 │     N/A │
│ tools            │     15 │    800 │   8/25/15│      8 │       0 │     N/A │
│ contrib          │     28 │   1500 │  15/55/25│     35 │       7 │     N/A │
│ tests            │     35 │   1200 │   5/30/60│     25 │       2 │   85.3% │
└──────────────────┴────────┴────────┴──────────┴────────┴─────────┴──────────┘
```

*Note: Cls/Mtd shows Classes/Methods/Functions (e.g., 25/112/85 = 25 classes, 112 methods, 85 functions)*

### Analyze Specific Directory

```bash
python3 ~/.claude/skills/code-metrics/scripts/analyze_codebase.py prefusion
```

### Include Test Coverage (Slower)

```bash
python3 ~/.claude/skills/code-metrics/scripts/analyze_codebase.py --all --coverage
```

### JSON Output for Programmatic Use

```bash
python3 ~/.claude/skills/code-metrics/scripts/analyze_codebase.py --all --json
```

## Metrics Collected

| Tool | Metrics |
|------|---------|
| **cloc** | Files, SLOC, comments, comment ratio |
| **radon cc** | Classes, Methods, Functions, Max cyclomatic complexity, CC distribution (A-F) |
| **radon mi** | Maintainability Index, low-MI file count |
| **ruff** | Total violations, files with issues, top error codes |
| **pytest** | Test case count, test modules |
| **coverage** | Statement coverage (optional, slow) |

**Note**: The skill distinguishes between:
- **Classes**: Standalone class definitions
- **Methods**: Functions defined inside classes
- **Functions**: Standalone (module-level) functions

## Directory-Specific Behavior

- **prefusion/tools**: Complexity threshold B (6-10), primary focus
- **tests**: Complexity threshold D (21-30), higher tolerance
- **contrib**: Report outliers, don't over-interpret
- **configs**: Always excluded (via --exclude flag)

## Interpreting Results

See [metrics_interpretation.md](references/metrics_interpretation.md) for detailed guidance:

- **Max CC**: Lower is better, >10 warrants attention
- **Low MI**: Count of C/D/F grade files, indicates maintainability debt
- **Coverage**: 80%+ target, trends matter more than absolute values
- **SLOC**: Use for comparison/trends, NOT for productivity measurement

## Scripts

Individual metric scripts can be run directly:

```bash
# Physical size only
python3 scripts/cloc_metrics.py prefusion configs,__pycache__

# Complexity only
python3 scripts/radon_metrics.py prefusion B

# Lint warnings only
python3 scripts/ruff_metrics.py tools

# Test collection only
python3 scripts/test_metrics.py tests

# Test coverage (slow)
python3 scripts/test_metrics.py tests --coverage
```

## Requirements

Install tools before first use:

```bash
pip install cloc radon ruff pytest coverage
```

Or with system package manager:

```bash
# Ubuntu/Debian
sudo apt-get install cloc
pip install radon ruff pytest coverage
```

## Common Use Cases

1. **Sprint Retrospective**: Track metrics changes between iterations
2. **Code Review**: Identify high-complexity functions needing attention
3. **Technical Debt Assessment**: Use Low MI + Max CC to prioritize refactoring
4. **Onboarding**: Help new developers understand codebase structure
5. **Architecture Discussion**: Compare size/complexity across modules
