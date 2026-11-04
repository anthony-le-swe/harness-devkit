# Task flow, QA & review gates, resume

Run all commands from the target project's root; Python 3.10+ required (3.12+ recommended on Windows). This kit uses only the standard library.

```powershell
py -3 tools/project_control.py task-add --id TASK-001 --title "Example" --owner backend_dev --acceptance "Documented API behavior and tests" --priority 1
# Record only genuine owner scope approval:
py -3 tools/project_control.py task-approve --id TASK-001 --by "Project owner"
py -3 tools/project_control.py task-start --id TASK-001 --note "Approved implementation begins"
py -3 tools/project_control.py checkpoint --task TASK-001 --done "Plan checked" --next-action "Implement API" --tests "Not run"
py -3 tools/project_control.py task-submit --id TASK-001 --evidence "Files X/Y and comparison diff ready for QA"
py -3 tools/project_control.py task-qa --id TASK-001 --actor qa --result pass --evidence "pytest -q: 12 passed"
py -3 tools/project_control.py task-review --id TASK-001 --actor reviewer --result approved --evidence "Diff inspected, 0 blockers"
py -3 tools/project_control.py task-done --id TASK-001
py -3 tools/project_control.py dashboard
py -3 tools/project_control.py validate
```

On any code change after QA/Review, use `task-start` then `task-submit`: new revision automatically clears BOTH approvals. QA and Reviewer roles must be independent from developer and from each other. The CLI gates apply to recorded evidence; a dishonest caller can falsify `--actor` or pass strings. Verify thread evidence when it matters.

Git commits and pushes are separate from tracker Done; use normal `git add`, `git diff --cached`, `git commit`, `git push` only after gates. Git push requires a configured remote, credentials and network permissions.

To resume after quota exhaustion or a new session:
```powershell
py -3 tools/project_control.py resume
git status --short
py -3 tools/project_control.py validate
py -3 tools/project_control.py dashboard
```

`init-handoff` will REFUSE if EITHER `tracking/handoff.json` or `docs/SESSION_HANDOFF.md` exists, even invalid, `{}`, empty or partial. Explicit `checkpoint` replaces handoff with backups. Do not use init-handoff as a repair tool.

Dashboard is a static snapshot. Refresh after running `dashboard`. It shows task counts, QA/review statuses, decisions and checkpoint; it does not show live token consumption or automatically run agents.
