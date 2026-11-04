# Start a new Codex project

1. Open this repository root in Codex Desktop App (Local mode, trusted project). Check model, agent definitions, sandbox and enabled integrations.
2. `py -3 tools/project_control.py dashboard`; open `dashboard/index.html`.
3. Add a Git remote for THIS new project if desired. Keep `network_access=false` until explicitly configuring a trusted Git/network route; commit works locally, push requires network/auth.
4. Paste this into a NEW Codex thread:

```text
Act as Tech Lead and Orchestrator. Read AGENTS.md, SECURITY.md, tracking/state.json,
tracking/handoff.json, docs/SESSION_HANDOFF.md, docs/PROJECT_STATUS.md,
tracking/events.jsonl and all approved ADRs, then run the tracker resume and git status.

First establish project goals, acceptance criteria, roadmap, task dependencies,
and identify which decisions I need to approve. Do not presume new product scope
or ADRs are approved. Once I approve a milestone/backlog, execute eligible tasks
continuously: choose task -> developer -> submit -> independent QA PASS -> independent
Reviewer APPROVED -> tracker Done -> diff/secret check -> normal commit and push (if
permitted) -> checkpoint -> dashboard -> next eligible task. Never require my
approval for routine development, tests or regular commits/pushes inside approved scope.
Never bypass QA/review gates, self-approve an ADR, delete files, or access outside
this project. If quota ends, leave a recoverable checkpoint; if a blocker exists,
record it and move to another approved eligible task.
```

5. To recover in a new thread:

```text
Resume this project from AGENTS.md, tracking/state.json, tracking/handoff.json,
docs/SESSION_HANDOFF.md, docs/PROJECT_STATUS.md, events and approved ADRs.
Run py -3 tools/project_control.py resume, git status --short and targeted tests.
Reconcile actual implementation before continuing the next eligible task.
Checkpoint after meaningful steps and refresh the dashboard.
```

Use a Codex App Automation if available for recurring invocations; it does not bypass quota or OS security and is not configured by this script.
