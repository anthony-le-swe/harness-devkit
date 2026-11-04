# Harness Devkit — portable Codex AI Software Team

Reusable starter for **Codex Desktop App**, with lead + specialist subagents, independent QA/Reviewer gate, decision records, quota-safe handoff, local dashboard, and sandbox-aware workspace instructions.

## Quick start — NEW project (Windows PowerShell)

```powershell
git clone https://github.com/anthony-le-swe/harness-devkit.git
cd harness-devkit
py -3 init.py new "D:\Projects\my-new-app" --name "My New App"
```

Then open **`D:\Projects\my-new-app`** in Codex Desktop App (Local, trusted workspace). The init command creates a local Git repo when Git is installed, **but does not commit, push, create a remote, start Codex or schedule automation**.

```powershell
cd D:\Projects\my-new-app
py -3 tools\project_control.py validate
py -3 tools\project_control.py dashboard
start dashboard\index.html
```

Read `START-CODEX.md` and paste its starter prompt into a NEW Codex thread. Approve initial project scope/ADRs once; afterward the team can process approved backlog tasks sequentially without asking for routine task-by-task approval.

## Install in an EXISTING project (no overwrite)

```powershell
py -3 init.py install "D:\Projects\existing-app" --name "Existing App"
```

The installer **preflights every destination path and refuses any file collision**; it never overwrites existing configuration, source, tracking, decisions or `.git`. If conflicts exist, perform a reviewed manual merge. Destination symlinks/junctions and attempting to install within harness-devkit are refused. No files are deleted by the installer.

## What gets installed?

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Team operating contract, scope/security and autonomous task loop |
| `.codex/config.toml` | High-capability lead, lower-cost default workers, restrictive workspace sandbox |
| `.codex/agents/*.toml` | 8 project-scoped agents: PO, Architect, Designer, Repo Explorer, Frontend, Backend, QA, Reviewer |
| `tools/project_control.py` | Task lifecycle, **two independent required quality gates**, ADRs, event history, safe checkpoints, dashboard generation |
| `tracking/state.json` | Canonical task + decision ledger (fresh per project) |
| `tracking/events.jsonl` | Chronological append-only-by-convention events |
| `tracking/handoff.json`, `docs/SESSION_HANDOFF.md` | Quota-safe resume state |
| `docs/PROJECT_STATUS.md`, `dashboard/index.html` | Human-readable progress and offline visual dashboard |
| `SECURITY.md`, `docs/WORKFLOW.md`, `START-CODEX.md` | Security model, commands, setup and resume prompt |

Agent model defaults: main `gpt-6.1-sol` high; PO, Architect and Reviewer use Sol; Developers, QA, Designer and Explorer use `gpt-6-luna`. Model availability is account-dependent. If your account does not support one, edit `.codex` configuration to a supported model and verify the runtime selection in Codex App.

## Quality gates (enforced in tracker)

`Todo → In progress → Submit revision → QA PASS → Reviewer APPROVED → Done → Commit → Push → Checkpoint → Next task`

The tracker rejects Done without QA+Reviewer evidence on the same current revision; QA, Reviewer, implementer must be different named actors. Fixes after QA require `task-submit` on a new revision, resetting both gates. See [`template/docs/WORKFLOW.md`](template/docs/WORKFLOW.md) for commands. This is a workflow gate, not identity authentication: a caller could lie about evidence, so independent thread records remain important.

## Safety, Git and autonomy limits

- `workspace-write` restricts sandboxed command writes but **does not provide hard OS-level isolation**. For a literal guarantee of no changes outside project, run Codex in a VM/container mounted only with project files. See [template/SECURITY.md](template/SECURITY.md).
- Command network is **disabled by default**. For autonomous `git push`, you must explicitly configure a trusted Git/network path and a remote on each new project, accept the expanded network exposure, and verify auth/sandbox behavior.
- Normal commit/push to the authorized remote is permitted after gates; force-push, destructive cleanup, deleting files, leaking secrets and production deployment are not.
- This package stores checkpoints and a resume plan; **it will not itself run 24/7 or restart when quotas refresh**. Scheduled Codex App automation is a separate optional setup.
- Dashboard is a **snapshot**, not live background telemetry. Rebuild with `py -3 tools/project_control.py dashboard` and refresh browser.
- Task/ADR approval is self-reported by the CLI, not a cryptographic identity check. Human must approve scope and architecture changes.

## Self-test the template

```powershell
py -3 -m unittest discover -s tests -v
```

Tests use a fresh `tests/.scratch/` fixture each time and **never clean up fixtures**. They do not change real user projects. See [Codex subagent docs](https://learn.chatgpt.com/docs/agent-configuration/subagents) and [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference).
