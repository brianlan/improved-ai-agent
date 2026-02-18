# Metrics Interpretation Guide

This guide explains how to interpret each metric collected by the code-metrics skill.

## Physical Size Metrics (cloc)

| Metric | Description | How to Use |
|--------|-------------|------------|
| **Files** | Total number of source files | Monitor growth over time |
| **SLOC** | Source Lines of Code (excluding blanks/comments) | Compare directories, track trends |
| **Comment Ratio** | Comments / SLOC percentage | 15-25% is typical; too low = under-documented, too high may indicate over-commenting |
| **Blank Lines** | Empty lines (formatting) | Generally ignored |

**Best Practices:**
- Use for comparing directories (prefusion vs tools vs contrib)
- Use for tracking trends over time
- **Do NOT** use LOC to judge code quality or developer productivity
- Raw LOC numbers are most useful for relative comparisons

## Logical Size Metrics (radon cc)

| Metric | Description | How to Use |
|--------|-------------|------------|
| **Classes** | Total number of class definitions | Understand architectural complexity |
| **Methods** | Total number of methods (functions inside classes) | Track class-based API surface |
| **Functions** | Total number of standalone (module-level) functions | Track functional API surface |
| **Total Callable Units** | Methods + Functions | Total API surface area |
| **LLOC** | Logical Lines of Code | More accurate than physical LOC for effort estimation |
| **Avg Function Length** | Average LLOC per callable unit | Lower is typically better (<20 is good) |

**Distinction:**
- **Classes**: Standalone class definitions (e.g., `class MyClass:`)
- **Methods**: Functions defined inside classes (e.g., `def my_method(self):`)
- **Functions**: Standalone module-level functions (e.g., `def my_function():`)

**Best Practices:**
- Very long functions (>50 LLOC) may need refactoring
- High callable unit count in src directory indicates complex API surface
- Tests directory having many small functions is good
- High class count with few methods per class may indicate over-abstraction
- Many standalone functions may indicate procedural rather than object-oriented design

## Cyclomatic Complexity (radon cc)

Measures the number of linearly independent paths through code.

| Rank | Range | Interpretation |
|------|-------|----------------|
| **A** | 1-5 | Low risk, simple |
| **B** | 6-10 | Moderate risk, acceptable |
| **C** | 11-20 | High risk, consider refactoring |
| **D** | 21-30 | Very high risk |
| **E/F** | 31+ | Extreme risk, should refactor |

**Best Practices:**
- **Don't use average complexity** - it hides outliers
- Focus on: maximum value, count of C+ functions
- Different thresholds for different directories:
  - src/tools: B (6-10) is threshold
  - tests: D (21-30) is acceptable (tests can be complex)
- High complexity + low MI = high-priority refactoring candidate

## Maintainability Index (radon mi)

Combined metric considering complexity, volume, and code structure.

| Rank | Range | Interpretation |
|------|-------|----------------|
| **A** | 100-20 | Highly maintainable |
| **B** | 19-10 | Maintainable |
| **C** | 9-0 | Warning level, difficult to maintain |
| **D** | <0 | Poor maintainability |
| **F** | unranked | Analysis failed |

**Best Practices:**
- **Do NOT** use MI to evaluate developer performance
- Use for:
  - Identifying files that need refactoring
  - Tracking technical debt accumulation
  - Prioritizing code review focus
- contrib directory having C/D files is common (may be experimental/legacy)
- prefusion directory should aim for mostly A/B

## Code Quality (ruff)

| Metric | Description | How to Use |
|--------|-------------|------------|
| **Total Violations** | Total lint warnings found | Track trends, not absolute numbers |
| **Files with Issues** | Number of files with warnings | Identify problematic files |
| **Top Errors** | Most common error codes | Focus improvement efforts |

**Best Practices:**
- Don't fix every single warning immediately
- Look for patterns: which error codes are most common?
- Focus on files with highest warning density
- Compare between directories to find problematic areas
- Useful for tracking code quality improvements over time

## Test Metrics (pytest)

| Metric | Description | How to Use |
|--------|-------------|------------|
| **Test Count** | Number of test cases | Track test suite growth |
| **Test Modules** | Number of test files | Understand test organization |
| **Test Classes** | Number of test classes | See test structure patterns |

**Best Practices:**
- Test count should grow with feature additions
- Ratio of test count to SLOC indicates test coverage depth
- Tests directory structure should mirror source structure

## Coverage (coverage.py)

| Metric | Description | How to Use |
|--------|-------------|------------|
| **Statement Coverage** | % of statements executed | Track over time |
| **Files Measured** | Number of source files in report | Ensure correct paths |

**Best Practices:**
- 80%+ is a common target
- Trends matter more than single measurements
- Edge cases and error handling often need targeted tests
- Don't chase 100% - diminishing returns

## Common Misinterpretations

### ❌ Wrong Approaches

- Using LOC to measure productivity or code quality
- Using tests directory complexity as a negative indicator
- Using MI scores to evaluate developers
- Treating any single metric as "good" or "bad" in isolation
- Comparing metrics across very different project types

### ✅ Right Approaches

- **prefusion**: High complexity + low MI = refactoring candidate
- **tools**: Rapid file count growth = accumulating technical debt
- **contrib**: Focus on outliers, don't over-interpret
- **tests**: Coverage trends > single measurements
- **All metrics**: Use for comparisons and tracking, not judgment

## Summary Table Format

When reporting metrics, this format is recommended:

| Directory | SLOC | Files | Cls/Mtd/Fn | Max CC | Low MI | Coverage |
|-----------|------|-------|------------|--------|--------|----------|
| prefusion |      |       |            |        |        |          |
| tools     |      |       |            |        |        | N/A      |
| contrib   |      |       |            |        |        | N/A      |
| tests     |      |       |            |        |        |          |

*Note: Cls/Mtd/Fn shows Classes/Methods/Functions*

This table format works well for:
- README documentation
- Technical evaluations
- Architecture discussions
- Sprint retrospectives
