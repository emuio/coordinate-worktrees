# Coordinate Worktrees

[简体中文](README_CN.md)

Coordinate long-running Codex App delivery across isolated Git worktrees and reviewed pull or merge requests, then retire completed lanes without discarding recoverable work.

This skill helps one coordinator task divide work into durable delivery lanes, keep branch and review ownership explicit, and decide when a short-lived subagent is enough versus when a user-visible Codex App task needs its own worktree.

## Requirements

- Codex App with user-visible task and native worktree support
- A Git repository for implementation work
- A GitHub or GitLab remote when the workflow includes pull or merge requests

This skill coordinates capabilities provided by Codex App. It does not add worktree task support to CLI-only or other agent environments.

## Install

Send this prompt to Codex:

```text
Use $skill-installer to install the coordinate-worktrees skill from https://github.com/emuio/coordinate-worktrees/tree/main/skills/coordinate-worktrees.
```

The installed skill is available on the next Codex turn.

For a manual installation with the built-in installer:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo emuio/coordinate-worktrees \
  --path skills/coordinate-worktrees
```

## Use

Ask Codex to apply the skill explicitly:

```text
Use $coordinate-worktrees to split this implementation into isolated worktree tasks and coordinate review and merge.
```

Typical requests include:

- Run two independent implementation streams in parallel worktrees and review both before integration.
- Keep a read-only architecture review in a subagent while persistent implementation stays in user-visible tasks.
- Build a stacked PR or MR sequence where dependent work starts from the latest integration branch.
- Act as the sole coordinator and merge owner while other tasks implement and respond to review findings.

## Routing model

| Work | Execution surface | Git ownership |
| --- | --- | --- |
| Read-only investigation or independent review | Short-lived collaboration subagent | None |
| Long-running implementation requiring commits or review | Codex App task in a native worktree | Dedicated branch and PR/MR |
| Tightly coupled edits to the same files or state | One sequential lane | One owner |

The coordinator owns the delivery graph, integration state, review decisions, and final merge. Each implementation lane owns its branch, commits, checks, and review fixes, but does not merge itself.

New App tasks remain unpinned by default. Pin a task only when the user explicitly requests it; coordination relies on the ledger, task handle, branch, and PR or MR rather than sidebar order.

## Model and reasoning settings

Choose the execution surface before choosing model or reasoning settings. A full-history collaboration subagent inherits the parent task's current settings. A newly created Codex App task is independent and uses configured defaults unless the user explicitly pins overrides; it does not inherit the coordinator task's transient settings.

The coordinator records whether settings were inherited, came from configured defaults, or were explicitly pinned. The skill does not treat automatic difficulty-based model routing as a Codex default and does not silently override the user's configuration.

For progress tracking, prefer compact `wait_threads` snapshots. Use `read_thread` only when the full transcript or diagnostic detail is required, and do not report unchanged snapshots.

## Safety model

- Preserve the user's Git identity and repository rules.
- Keep secrets and credentials out of prompts, repository files, logs, and review descriptions.
- Treat branches and PRs or MRs as durable ownership records; thread IDs are runtime handles only.
- Require explicit authorization for pushes, merges, closures, and other external state changes.

## License

[MIT](LICENSE)
