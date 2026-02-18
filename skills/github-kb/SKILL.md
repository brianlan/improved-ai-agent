---
name: github-kb
description: Manage and query a local GitHub repository knowledge base. Use when the user mentions GitHub, repo, repository, or requests to download/clone a repository, search for GitHub issues/PRs, or analyze code from GitHub projects. This skill maintains a local knowledge base at /ssd4/github-knowledge-base with automatic tracking of repository summaries.
---

# GitHub Knowledge Base

Manages a local GitHub repository knowledge base at `/ssd4/github-knowledge-base/` with metadata tracked in `AGENTS.md`.

**Core Principle - Prudent Cloning**: Repositories are only cloned after gathering information via `gh`/`curl` and receiving explicit user confirmation. Never clone without presenting findings and asking for confirmation.

## Quick Reference

| Task | Command |
|------|---------|
| List local repos | `ls /ssd4/github-knowledge-base/` |
| Check repo info | `gh repo view owner/repo --json name,description,primaryLanguage,stargazerCount,forksCount` |
| Get README | `gh repo view owner/repo --json readme \| jq -r '.readme.text'` |
| Get structure | `gh api repos/owner/repo/git/trees/main?recursive=1 -q '...'` |
| Clone repo | `git clone <url>` (into `username/repo-name`) |
| List issues | `gh issue list --repo owner/repo --state all --limit 100` |
| List PRs | `gh pr list --repo owner/repo --state all --limit 100` |

## Core Workflows

### Repository Discovery
1. Check local: `ls /ssd4/github-knowledge-base/`
2. Check summaries: `cat /ssd4/github-knowledge-base/AGENTS.md`

### Cloning Process (After Confirmation)
1. **Gather info**: Use `gh` commands below to collect metadata, README, structure
2. **Present to user**: Show name, description, language, stars, size, structure
3. **Get confirmation**: Use `question` tool with options
4. **Clone**: `cd /ssd4/github-knowledge-base && git clone <url>`
5. **Analyze**: Read README.md, identify purpose
6. **Update AGENTS.md**: Add one-sentence summary in format below

### User Confirmation Pattern
```python
question(questions=[{
    "question": f"Repository: **{name}**\nDescription: {desc}\nLanguage: {lang}\nStars: {stars} | Forks: {forks}\n\nWould you like me to clone this repository?",
    "header": "Clone Repository?",
    "options": [
        {"label": "Yes, clone it", "description": "Clone to /ssd4/github-knowledge-base"},
        {"label": "No", "description": "Use gh/curl only"}
    ]
}])
```

## Information Gathering Commands

```bash
# Basic repo info
gh repo view owner/repo --json name,description,url,primaryLanguage,stargazerCount,forksCount,updatedAt

# README content
gh repo view owner/repo --json readme | jq -r '.readme.text'

# Recent commits (last 5)
gh api repos/owner/repo/commits --paginate -q '.[:5] | .[] | "\(.sha[:7]) \(.commit.message[:80])"'

# Top-level directories
gh api repos/owner/repo/git/trees/main?recursive=1 -q '.tree | map(select(.type == "tree" and .path | split("/") | length == 1)) | .[] | .path'

# Stats summary
gh api repos/owner/repo -q '"Size: \(.size)KB, Stars: \(.stargazers_count), Forks: \(.forks_count)"'
```

## Querying Repositories

**GitHub metadata (no clone needed):**
```bash
gh issue list --repo owner/repo --state all --limit 100
gh issue view <num> --repo owner/repo
gh pr list --repo owner/repo --state all --limit 100
gh pr view <num> --repo owner/repo
gh release list --repo owner/repo
gh search repos <query> --limit 10
```

**Local analysis (repo already cloned):**
- Use `task` tool with `explore` subagent for code search
- Use `grep` to find patterns
- Use `read` to examine files
- `find . -name "*.py" | wc -l` for file counts
- `git log --oneline --graph` for history

## AGENTS.md Format

```markdown
# GitHub Repository Knowledge Base

## Repository Summaries

### [owner/repo-name](owner/repo-name)

One-sentence summary of purpose.
```

**Rules:** One markdown link per repo, one sentence per summary, add to end of section.

## Workflow Decision Tree

| User Request | Action |
|--------------|--------|
| Mentions a repo | Check local → if missing, gather info with gh, ask to clone |
| Asks to clone | gh/curl info → present → confirm → clone → update AGENTS.md |
| Questions about repo | Check local → if local: explore tools → if not: gh/curl → offer clone if deep analysis needed |
| Deep analysis needed | Gather gh/curl info → present → ask confirmation → only then clone |

## Examples

**Clone request:**
```bash
gh repo view facebook/react --json name,description,primaryLanguage,stargazerCount,forksCount
gh repo view facebook/react --json readme | jq -r '.readme.text' | head -30
gh api repos/facebook/react/git/trees/main?recursive=1 -q '...'
```
Present to user, confirm, then:
```bash
cd /ssd4/github-knowledge-base && git clone https://github.com/facebook/react.git
```
Update AGENTS.md with summary.

**Issues query:**
```bash
gh issue list --repo facebook/react --state open --limit 20
```

**Structure query (local):**
```bash
cd /ssd4/github-knowledge-base/facebook/react && tree -L 2 -d
```

## Best Practices

1. Never clone without user confirmation
2. Use gh/curl for initial discovery
3. Present clear, organized information
4. Always update AGENTS.md after cloning
5. Create concise one-sentence summaries
6. Use gh CLI for GitHub metadata
7. Use local tools for cloned repo analysis
8. Offer cloning only when deep analysis is needed
