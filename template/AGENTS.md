# Codex AI Software Team — operational contract

Read `SECURITY.md`, `tracking/state.json`, `tracking/handoff.json`, `docs/SESSION_HANDOFF.md`, `tracking/events.jsonl`, `docs/decisions/` and `git status --short` at the beginning of each run. The project is NOT automatically approved for implementation: first establish a scoped, approved backlog and ADRs. Never infer approval from tool availability.

## Roles and orchestration

- Main agent is Tech Lead / Orchestrator (`gpt-6.1-sol`, high). Own scheduling, dependencies, integration and persisted status; favor smaller workers for bounded tasks.
- `po`, `architect` and `designer` refine scope, requirements and system design.
- `repo_explorer`, `frontend_dev`, `backend_dev` inspect and implement scoped changes.
- `qa` independently executes/tests against acceptance criteria; `reviewer` independently audits diff, architecture, security and QA evidence.
- Do not let agents simultaneously edit the same files. QA and reviewer must be distinct from implementer and from each other for every implementation task.

## Mandatory QA + independent review gate

For each approved, unblocked implementation task:
1. Select highest-priority ready task. Persist task ownership and next action first.
2. Develop only the approved scope, saving checkpoints after major verified steps.
3. Submit changed implementation for verification (`task submit` increments revision and invalidates old QA/review approvals).
4. Independent `qa` runs real tests and records PASS/FAIL/BLOCKED with exact evidence and revision.
5. Independent `reviewer` checks actual diff, security, regressions and test evidence, then records APPROVED/CHANGES_REQUESTED/BLOCKED.
6. If blocked or rejected, fix, `submit` a new revision, and repeat both gates. Never fabricate evidence.
7. Only call `task done` when independent QA PASS and Reviewer APPROVED on the CURRENT revision, all criteria are met and evidence persisted. The tracker enforces these checks against recorded state.
8. Inspect `git diff`, check for secrets and unrelated edits, normal commit and push when networking/authentication permits. Log SHA/status; do not force push or remove evidence.
9. Refresh dashboard, save handoff, then select the next eligible task without waiting for routine owner approvals.

Only the HUMAN owner approves new scope, architecture decisions, production changes and destructive operations. If a new decision is needed, record a blocker and continue another approved task. Stop when no approved tasks are eligible, quota is exhausted, security blocks execution, or work is complete.

## Persistence and recovery

Orchestrator is the only tracker writer; subagents return results, owner requests and evidence, never concurrently edit state/events. Keep `tracking/state.json`, `tracking/events.jsonl`, `tracking/handoff.json`, `docs/SESSION_HANDOFF.md`, `docs/PROJECT_STATUS.md`, `docs/decisions/` as durable truth. Run `python tools/project_control.py resume` on new session; compare with `git status`, files and tests. A task interrupted mid-code is NOT Done. Run `checkpoint` before costly/long operations and after changes; do not wait until the end of a turn.

`init-handoff` must NEVER overwrite an existing JSON OR Markdown handoff, including `{}`, invalid JSON, empty or partial files; explicit checkpoint is required to replace. No clearing retained fixtures, project files or incident evidence without owner authorization.

## Security / automation

Write only inside this project. No elevated sandbox, cross-project file changes, arbitrary network access, secret exposure, forced Git operations, auto deployment or destructive commands. Approvals to normal commit/push do not imply permission to weaken workspace limits. Safety review takes priority over speed. Report only tests actually run and outcomes actually observed. Keep dashboard updated from tracker data (snapshot, not live telemetry). Scheduling/24-7 operation requires Codex App automation and available quota; never claim template setup makes it perpetual.
