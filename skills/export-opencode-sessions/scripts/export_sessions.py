#!/usr/bin/env python3

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def parse_time(value: str) -> int:
    text = value.strip()
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    iso = text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def fmt_time(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def default_db() -> Path:
    xdg = Path.home() / ".local" / "share"
    if "XDG_DATA_HOME" in __import__("os").environ:
        xdg = Path(__import__("os").environ["XDG_DATA_HOME"])
    return xdg / "opencode" / "opencode.db"


def session_info(row: sqlite3.Row) -> dict:
    out = {
        "id": row["id"],
        "slug": row["slug"],
        "projectID": row["project_id"],
        "workspaceID": row["workspace_id"],
        "directory": row["directory"],
        "parentID": row["parent_id"],
        "title": row["title"],
        "version": row["version"],
        "time": {
            "created": row["time_created"],
            "updated": row["time_updated"],
            "compacting": row["time_compacting"],
            "archived": row["time_archived"],
        },
    }
    if row["share_url"]:
        out["share"] = {"url": row["share_url"]}
    if row["summary_additions"] is not None or row["summary_deletions"] is not None or row["summary_files"] is not None:
        out["summary"] = {
            "additions": row["summary_additions"] or 0,
            "deletions": row["summary_deletions"] or 0,
            "files": row["summary_files"] or 0,
            "diffs": json.loads(row["summary_diffs"]) if row["summary_diffs"] else None,
        }
    if row["revert"]:
        out["revert"] = json.loads(row["revert"])
    if row["permission"]:
        out["permission"] = json.loads(row["permission"])
    if out["workspaceID"] is None:
        out.pop("workspaceID")
    if out["parentID"] is None:
        out.pop("parentID")
    if out["time"]["compacting"] is None:
        out["time"].pop("compacting")
    if out["time"]["archived"] is None:
        out["time"].pop("archived")
    return out


def load_messages(conn: sqlite3.Connection, session_id: str) -> list:
    msgs = conn.execute(
        """
        select id, session_id, time_created, time_updated, data
        from message
        where session_id = ?
        order by time_created asc
        """,
        (session_id,),
    ).fetchall()

    parts = conn.execute(
        """
        select id, session_id, message_id, data
        from part
        where session_id = ?
        order by time_created asc
        """,
        (session_id,),
    ).fetchall()

    part_map: dict[str, list] = {}
    for row in parts:
        data = json.loads(row["data"])
        data["id"] = row["id"]
        data["sessionID"] = row["session_id"]
        data["messageID"] = row["message_id"]
        if row["message_id"] not in part_map:
            part_map[row["message_id"]] = []
        part_map[row["message_id"]].append(data)

    out = []
    for row in msgs:
        data = json.loads(row["data"])
        data["id"] = row["id"]
        data["sessionID"] = row["session_id"]
        if "time" not in data or not isinstance(data["time"], dict):
            data["time"] = {}
        if "created" not in data["time"]:
            data["time"]["created"] = row["time_created"]
        if "updated" not in data["time"]:
            data["time"]["updated"] = row["time_updated"]
        out.append(
            {
                "info": data,
                "parts": part_map.get(row["id"], []),
            }
        )
    return out


def md_header(info: dict, meta: bool) -> str:
    if not meta:
        return "## Assistant\n\n"
    agent = info.get("agent", "assistant")
    model = info.get("modelID", "unknown")
    created = info.get("time", {}).get("created")
    completed = info.get("time", {}).get("completed")
    duration = ""
    if isinstance(created, int) and isinstance(completed, int):
        duration = f" · {((completed - created) / 1000):.1f}s"
    return f"## Assistant ({agent} · {model}{duration})\\n\\n"


def md_part(part: dict, thinking: bool, details: bool) -> str:
    kind = part.get("type")
    if kind == "text" and not part.get("synthetic"):
        return f"{part.get('text', '')}\\n\\n"
    if kind == "reasoning":
        if thinking:
            return f"_Thinking:_\\n\\n{part.get('text', '')}\\n\\n"
        return ""
    if kind == "tool":
        out = f"**Tool: {part.get('tool', 'unknown')}**\\n"
        state = part.get("state", {})
        if details and state.get("input") is not None:
            out += f"\\n**Input:**\\n```json\\n{json.dumps(state.get('input'), indent=2)}\\n```\\n"
        if details and state.get("status") == "completed" and state.get("output") is not None:
            out += f"\\n**Output:**\\n```\\n{state.get('output')}\\n```\\n"
        if details and state.get("status") == "error" and state.get("error") is not None:
            out += f"\\n**Error:**\\n```\\n{state.get('error')}\\n```\\n"
        return out + "\\n"
    return ""


def to_markdown(session: dict, messages: list, thinking: bool, details: bool, meta: bool) -> str:
    out = f"# {session.get('title', session['id'])}\\n\\n"
    out += f"**Session ID:** {session['id']}\\n"
    out += f"**Directory:** {session.get('directory', '')}\\n"
    out += f"**Created:** {fmt_time(session['time']['created'])}\\n"
    out += f"**Updated:** {fmt_time(session['time']['updated'])}\\n\\n"
    out += "---\\n\\n"
    for msg in messages:
        info = msg["info"]
        if info.get("role") == "user":
            out += "## User\\n\\n"
        else:
            out += md_header(info, meta)
        for part in msg.get("parts", []):
            out += md_part(part, thinking, details)
        out += "---\\n\\n"
    return out


def safe_name(session_id: str, updated: int, ext: str) -> str:
    return f"{updated}_{session_id}.{ext}"


def session_dir_name(session_id: str, updated: int) -> str:
    return f"{updated}_{session_id}"


def tree_chain(session_id: str, parent_map: dict[str, str | None], name_map: dict[str, str]) -> list[str]:
    chain: list[str] = []
    seen: set[str] = set()
    cur = session_id
    while cur in name_map and cur not in seen:
        seen.add(cur)
        chain.append(name_map[cur])
        parent = parent_map.get(cur)
        if not parent:
            break
        cur = parent
    chain.reverse()
    return chain


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenCode sessions by directory and time range")
    parser.add_argument("--project-dir", required=True, help="Project directory to match against session.directory")
    parser.add_argument("--start", required=True, help="Start time (epoch ms or ISO-8601)")
    parser.add_argument("--end", required=True, help="End time (epoch ms or ISO-8601)")
    parser.add_argument("--output-dir", required=True, help="Output directory for exported files")
    parser.add_argument("--format", choices=["raw", "markdown"], default="raw")
    parser.add_argument("--layout", choices=["session", "flat", "tree"], default="tree")
    parser.add_argument("--db-path", default=str(default_db()), help="Path to opencode.db")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--roots-only", dest="roots_only", action="store_true")
    scope.add_argument("--include-children", dest="roots_only", action="store_false")
    parser.set_defaults(roots_only=False)
    parser.add_argument("--thinking", action="store_true", help="Include reasoning parts in markdown")
    parser.add_argument("--tool-details", action="store_true", help="Include tool input/output in markdown")
    parser.add_argument("--assistant-metadata", action="store_true", help="Include assistant agent/model in markdown")
    args = parser.parse_args()

    db = Path(args.db_path).expanduser().resolve()
    if not db.exists():
        raise FileNotFoundError(f"Database not found: {db}")

    project = Path(args.project_dir).expanduser().resolve()
    start = parse_time(args.start)
    end = parse_time(args.end)
    if end < start:
        raise ValueError("--end must be greater than or equal to --start")

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    where = """
        where (directory = ? or directory = ?)
          and time_updated >= ?
          and time_updated <= ?
    """
    params: list = [str(project), args.project_dir, start, end]
    if args.roots_only:
        where += " and parent_id is null"
    rows = conn.execute(
        f"""
        select *
        from session
        {where}
        order by time_updated desc
        """,
        params,
    ).fetchall()

    parent_map = {row["id"]: row["parent_id"] for row in rows}
    name_map = {row["id"]: session_dir_name(row["id"], row["time_updated"]) for row in rows}

    exported = []
    for row in rows:
        info = session_info(row)
        messages = load_messages(conn, info["id"])
        if args.layout == "session":
            target_dir = out_dir / session_dir_name(info["id"], info["time"]["updated"])
            target_dir.mkdir(parents=True, exist_ok=True)
        elif args.layout == "tree":
            chain = tree_chain(info["id"], parent_map, name_map)
            target_dir = out_dir
            for part in chain:
                target_dir = target_dir / part
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = out_dir
        if args.format == "raw":
            payload = {
                "info": info,
                "messages": messages,
            }
            name = "session.json" if args.layout in ("session", "tree") else safe_name(info["id"], info["time"]["updated"], "json")
            target = target_dir / name
            target.write_text(json.dumps(payload, indent=2) + "\n")
        else:
            text = to_markdown(info, messages, args.thinking, args.tool_details, args.assistant_metadata)
            name = "transcript.md" if args.layout in ("session", "tree") else safe_name(info["id"], info["time"]["updated"], "md")
            target = target_dir / name
            target.write_text(text)
        exported.append(
            {
                "session_id": info["id"],
                "title": info.get("title"),
                "directory": info.get("directory"),
                "updated": info["time"]["updated"],
                "updated_iso": fmt_time(info["time"]["updated"]),
                "file": str(target.relative_to(out_dir)),
                "message_count": len(messages),
            }
        )

    index = {
        "project_dir": str(project),
        "project_dir_input": args.project_dir,
        "start": start,
        "end": end,
        "start_iso": fmt_time(start),
        "end_iso": fmt_time(end),
        "format": args.format,
        "layout": args.layout,
        "roots_only": args.roots_only,
        "roots": sum(1 for row in rows if row["parent_id"] is None),
        "children": sum(1 for row in rows if row["parent_id"] is not None),
        "count": len(exported),
        "files": exported,
    }
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n")

    print(f"Exported {len(exported)} sessions")
    print(f"Index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
