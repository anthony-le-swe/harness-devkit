# Harness Devkit — Codex + Claude Code multi-agent team

Portable developer-agent harness for **Codex Desktop** and **Claude Code** (CLI or Claude Desktop Code tab). Both clients use the same project tracker, QA+Reviewer gate, decision log, session handoff and snapshot dashboard. Only the native agent configurations differ.

## Quick start on Windows (new project)

```powershell
git clone https://github.com/anthony-le-swe/harness-devkit.git
cd harness-devkit
py -3 init.py new "D:\Projects\my-app" --name "My App" --platform both
```

Or choose one client with `--platform claude` or `--platform codex`. `both` is the default. Each project gets fresh tracking state; initializer can run `git init` locally but never commits or pushes automatically.

**Claude:** Open the new project root in Claude Code (Claude Desktop **Code** tab or CLI `claude`), read `START-CLAUDE.md`, select `/model opus` for the lead, check `/agents`, `/permissions`, `/context`. Subagents come from `.claude/agents/*.md`. Claude Code reads `CLAUDE.md`, which imports `AGENTS.md` and `SECURITY.md`.

**Codex:** Open the project root in Codex Desktop App, check permissions and custom agents, and read `START-CODEX.md`. Subagents come from `.codex/agents/*.toml`.

**Existing project** (non-overwrite):

```powershell
py -3 init.py install "D:\Projects\existing-app" --name "Existing App" --platform both
```

The installer preflights all paths and refuses collisions, junctions, and symlink escapes. It will never replace an existing config or tracker automatically. For an existing Codex harness, a reviewed manual merge of Claude-specific files is required.

## Shared workflow

```text
Owner approves scope and significant ADRs once
     ↓
Tech Lead chooses approved unblocked task
     ↓
Developer implements + submits current revision
     ↓
Independent QA PASS
     ↓
Independent Reviewer APPROVED
     ↓
Tracker Done → diff/secret check → normal commit/push → checkpoint → next task
```

The tracker **rejects Done without both gates on the current revision**, and invalidates gates for a new revision. Evidence and actor IDs are self-reported, so this is workflow validation, **not authenticated approval or sandbox enforcement**. Do not run Codex and Claude orchestrators concurrently against the same working tree: state files lack locking.

## Local dashboard, handoff and tests

```powershell
cd D:\Projects\my-app
py -3 tools\project_control.py validate
py -3 tools\project_control.py dashboard
start dashboard\index.html
py -3 tools\project_control.py resume
```

Project code and status belong to that new repository, not harness-devkit. The dashboard is an offline snapshot. All project history persists in `tracking/` and `docs/`. Neither Claude nor Codex auto-restarts after quota resets just because it has these files.

### Safety on Windows

**Native Windows Claude Code does not support Claude's OS-level Bash sandbox.** For strict filesystem isolation, run Claude Code in WSL2 with sandbox enabled or in an isolated VM/container with only the project mounted. `.claude/settings.json` defaults to regular permissions, no extra working directories and disallows bypass; instructions and tracker checks alone cannot prevent arbitrary external writes. Review MCP/tools and the actual effective permissions. The Codex workspace-write setting is also not an absolute OS isolation guarantee. Git push requires configured auth and network permission.

## Components

| Files | Role |
|---|---|
| `AGENTS.md`, `SECURITY.md` | Shared policy and safety model |
| `CLAUDE.md`, `.claude/agents/*.md`, `.claude/settings.json` | Claude Code instructions, eight native subagents, permission defaults |
| `.codex/config.toml`, `.codex/agents/*.toml` | Codex models, agents and sandbox settings |
| `tools/project_control.py` | Enforced QA/Reviewer workflow, ADR/event/checkpoint CLI, dashboard |
| `tracking/`, `docs/` | Per-project backlog, decisions, events, quota-safe handoff |
| `START-CLAUDE.md`, `START-CODEX.md` | Platform-specific starter and resume prompts |

Claude model tiers: choose **Opus** for main Tech Lead and Architect/Reviewer; **Sonnet** for developers, QA, PO/Designer; **Haiku** for Repo Explorer. Model alias availability depends on account/org, and runtime selections may override frontmatter. Verify inside Claude Code rather than assuming a configured alias was used.

## Template self-test

```powershell
py -3 -m unittest discover -s tests -v
```

Test fixtures stay under `tests/.scratch/` (no automatic cleanup). See [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Claude Code memory](https://code.claude.com/docs/en/memory) and [Claude Code sandbox](https://code.claude.com/docs/en/sandboxing).
