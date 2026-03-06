# OpenCode Session Export Reference

## Tables Used

- `session`
  - Filters: `directory` (exact), `time_updated` (range)
  - Default scope: root sessions only (`parent_id is null`)
  - Core fields: `id`, `title`, `directory`, `time_created`, `time_updated`
- `message`
  - Join key: `session_id`
  - `data` JSON stores message payload minus IDs
- `part`
  - Join key: `session_id`, grouped by `message_id`
  - `data` JSON stores part payload minus IDs

## Time Semantics

- OpenCode session filters use milliseconds since epoch.
- This skill accepts either epoch ms or ISO-8601, then normalizes to epoch ms.

## Raw Export Shape

```json
{
  "info": {
    "id": "session_x",
    "directory": "/repo",
    "time": { "updated": 123 }
  },
  "messages": [
    {
      "info": { "id": "message_x", "sessionID": "session_x", "role": "user" },
      "parts": [
        {
          "id": "part_x",
          "messageID": "message_x",
          "sessionID": "session_x",
          "type": "text"
        }
      ]
    }
  ]
}
```

## Markdown Export Notes

- Use user/assistant sections.
- Include reasoning/tool sections only when requested.
- Keep one file per session.

## Output Files

- Default layout (`--layout session`):
  - `<time_updated>_<session_id>/session.json` (raw)
  - `<time_updated>_<session_id>/transcript.md` (markdown)
- Flat layout (`--layout flat`):
  - `<time_updated>_<session_id>.json` or `.md`
- Tree layout (`--layout tree`, usually with `--include-children`):
  - `<root_updated>_<root_session_id>/session.json` or `transcript.md`
  - Child sessions nested under their parent session folder recursively
- Summary index: `index.json`
