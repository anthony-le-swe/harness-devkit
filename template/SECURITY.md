# Security model — read before granting autonomy

**The default Codex `workspace-write` sandbox is not a hard OS-level boundary.** It only controls sandboxed commands; connected apps, MCP tools, browser automation, permission overrides, Windows junctions/reparse points and other processes may have separate privileges. For a hard no-outside-project guarantee, use an isolated VM/container with only the project mounted.

- Work inside the project root only; reject traversals (`../`), absolute external paths and symlink/junction escapes. Disable unnecessary MCP/connectors.
- Do not elevate permissions, remove sandbox restrictions, delete files, run `git reset --hard`, `git clean`, force-push or modify credentials without explicit owner authorization.
- Git normal commit/push is authorized **only to the configured project remote and authorized branch**, after QA and Reviewer gates and secret/diff inspection. Do not accidentally include .env, tokens, databases or private data.
- The template sets `network_access = false`. For automatic CLI push you must explicitly enable the command network path in Codex runtime and accept the added exposure (or use a trusted Git integration). There is no GitHub-only network allowlist in this kit.
- Sandbox may allow writes to special paths under its own policy; check effective runtime permissions. The Python tracker also restricts its own writes; it cannot constrain arbitrary tools/processes.
- Before deleting any project files, require specific scope approval. Do not remove evidence, retained test fixtures or incident logs by default.
- Git commits are not backups until pushed; remote pushes are not a substitute for secrets scanning or independent QA.
- Tracker CLI's `--actor` field is self-reported, not an identity-verified approval. Independent agent execution and evidence must be checked in thread history.
- A checkpoint stores saved state, not unsaved agent thoughts. Automated execution depends on runtime, quota, available tasks and configured scheduling; template installation alone does not run 24/7.
