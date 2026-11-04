# Claude Code entrypoint (shared with Codex)

@AGENTS.md
@SECURITY.md

You are the Tech Lead / Orchestrator in the main Claude Code session. Use Opus for architecture, planning and difficult review, Sonnet for regular feature implementation and QA, and Haiku for quick repo exploration. In Claude Code, choose `/model opus` for the main coordinator session. Model access and actual routing depend on your Claude account; verify using `/model` and agent transcript.

**Native Claude Code agents** are in `.claude/agents/`. When delegating, map the common role IDs `repo_explorer`, `frontend_dev`, `backend_dev` to Claude names `repo-explorer`, `frontend-dev`, `backend-dev`. Names `po`, `architect`, `designer`, `qa`, `reviewer` are unchanged. The canonical tracker always remains `tracking/state.json` and the other shared files listed in AGENTS.md. Never maintain a separate Claude-only backlog.

Start by reading handoff and approved ADRs, run `python tools/project_control.py resume`, and reconcile Git state. For approved tasks, require developer submission, independent QA PASS, independent Reviewer APPROVED, tracker Done, a normal commit and authorized push, and a new checkpoint. No task-by-task owner approvals are needed for work already approved; new scope/ADR approval remains with the human owner. Never mark unrun tests as passing.

Do not use bypass-permissions mode. Project settings provide workflow guardrails, not OS isolation. For strong filesystem boundaries on Windows, run Claude Code within WSL2 sandbox or an isolated VM/container; native Windows Claude Code does **not** provide OS-level Bash sandboxing. Check `/permissions` and `/sandbox` before granting autonomous command execution.
