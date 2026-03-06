---
name: export-opencode-sessions
description: Export OpenCode session histories for a specific project directory and time range into separate files. Use when users ask to collect all chat logs/messages for a repo path, back up sessions for audits, or convert sessions to readable Markdown transcripts instead of raw JSON.
---

# Export OpenCode Sessions

## Overview

Export all sessions that match a project directory plus time window, then write one folder per session (default) containing raw JSON or Markdown transcript.

## Inputs

Require these inputs before running:

- Project directory path
- Time range start
- Time range end
- Output directory
- Output format (`raw` or `markdown`)

Accept time values as either epoch milliseconds or ISO-8601 timestamps.

## Workflow

1. Normalize project directory with `realpath` and keep the original path too.
2. Run the exporter script with explicit `--start` and `--end`.
3. Default export includes child sessions and uses tree layout.
4. Add `--roots-only` when you want `/sessions`-style root-only export.
5. Verify `index.json` exists in output.
6. Report exported session count and file paths.

## Quick Start

```bash
python3 scripts/export_sessions.py \
  --project-dir "/path/to/project" \
  --start "2026-02-01T00:00:00Z" \
  --end "2026-03-01T23:59:59Z" \
  --output-dir "/tmp/session-export" \
  --format raw
```

```bash
python3 scripts/export_sessions.py \
  --project-dir "/path/to/project" \
  --start 1738368000000 \
  --end 1740787199000 \
  --output-dir "/tmp/session-export-md" \
  --format markdown
```

## Script

Use `scripts/export_sessions.py` for deterministic exports.

### Behavior

- Filter sessions by exact `session.directory` match and `session.time_updated` range.
- By default, include root + child sessions (`parent_id` any).
- Default output layout is parent/child tree folders.
- In tree/session layouts, files are:
  - `raw`: `session.json`
  - `markdown`: `transcript.md`
- Optional flat layout keeps one file per session at output root.
- Write `index.json` with all exported session metadata and output files.

### Optional Flags

- `--db-path` to target a custom `opencode.db`
- `--roots-only` to export only root sessions
- `--include-children` to include child/fork/subagent sessions (default)
- `--layout session|flat|tree` to control grouped folders, flat files, or parent/child nested folders (default: `tree`)
- `--thinking` to include reasoning parts in Markdown
- `--tool-details` to include tool input/output blocks in Markdown
- `--assistant-metadata` to include assistant agent/model header in Markdown

### Parent-child Tree Export

Use tree layout for fine-grained separation of child/fork/subagent sessions:

```bash
python3 scripts/export_sessions.py \
  --project-dir "/path/to/project" \
  --start "2026-02-01T00:00:00Z" \
  --end "2026-03-01T23:59:59Z" \
  --output-dir "/tmp/session-export-tree" \
  --format markdown \
  --include-children \
  --layout tree
```

Tree layout example:

- `<root_updated>_<root_session_id>/transcript.md`
- `<root_updated>_<root_session_id>/<child_updated>_<child_session_id>/transcript.md`
- `<root_updated>_<root_session_id>/<child...>/<grandchild...>/transcript.md`

## Output Contract

After export, always provide:

- Project directory used for filtering
- Time range used (ms and ISO is acceptable)
- Number of sessions exported
- Output directory
- `index.json` location

## Troubleshooting

- If no sessions are found, confirm directory path exactly matches session `directory`.
- If DB is not found, pass `--db-path` explicitly.
- If timestamps look wrong, convert local times to UTC ISO-8601.

## Reference

- Read `references/opencode-session-schema.md` for DB tables and output shapes.
