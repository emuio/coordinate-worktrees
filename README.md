# Coordinate Worktrees

[简体中文](README_CN.md)

Coordinate explicitly requested, long-running Codex App delivery across isolated Git worktrees, with independently reviewed pull or merge requests when remote review is authorized, then retire completed lanes without discarding recoverable work.

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
Use $coordinate-worktrees to split this implementation into isolated worktree tasks, coordinate review, and report merge readiness without pushing, opening a PR or MR, or merging beyond my explicit authorization.
```

Typical requests include:

- Run two independent implementation streams in parallel worktrees and review both before integration.
- Keep a read-only architecture review in a subagent while persistent implementation stays in user-visible tasks.
- Build a stacked PR or MR sequence where dependent work starts from the latest integration branch.
- Act as the sole coordinator and merge-decision owner while other tasks implement and respond to review findings; merge only under recorded authority.

## Routing model

| Work | Execution surface | Git ownership |
| --- | --- | --- |
| Read-only investigation or independent review | Short-lived collaboration subagent | None |
| Explicitly requested, persistent multi-lane implementation | Codex App task in a native worktree | Dedicated branch; PR/MR only when authorized |
| Tightly coupled edits to the same files or state | One sequential lane | One owner |

The coordinator owns the delivery graph, integration state, review decisions, and any authorized final merge. Each implementation lane owns its branch, commits, checks, and review fixes, but does not merge itself.

New App tasks remain unpinned by default. Pin a task only when the user explicitly requests it; coordination relies on the ledger, task handle, branch, and PR or MR rather than sidebar order.

## Action authority

The skill separates delivery mode from authority for each external action:

| Mode | Default boundary |
| --- | --- |
| `plan-only` | Read-only partitioning and a proposed ledger |
| `local-delivery` | Explicitly requested App tasks, local branches, commits, and tests |
| `branch-delivery` | `local-delivery` plus an authorized branch push without review creation |
| `review-delivery` | `branch-delivery` plus Draft PR/MR creation when remote review delivery was explicitly requested |

Implementation task creation and optional listener creation have separate authority. Neither implies permission to push, open a review, merge, deploy, move the registered base checkout, archive tasks, delete branches, or remove manual worktrees. Push and review creation are also tracked separately so a push-only request cannot silently create a PR or MR. The coordinator treats every unspecified action as pending.

Task creation can also be asynchronous. A provisioning handle such as `clientThreadId` is recorded as `setup-pending`; it is never used as a real `threadId` or presented as a ready lane.

## Worktree placement and cleanup

- Persistent Codex App tasks use the App's native worktree. The physical directory is App-managed and must not be removed manually by the coordinator.
- Collaboration subagents share the coordinator checkout and do not create extra worktrees.
- Manual worktrees are an explicit fallback only. Keep them below a dedicated root such as `${CODEX_HOME:-$HOME/.codex}/manual-worktrees/<repository>/<lane>`, not as many sibling directories beside the primary repository.
- Every lane records whether it is `codex-managed`, `permanent`, or `coordinator-manual` and declares a retirement policy before work begins.

After every merged or explicitly abandoned lane, including one without a remote review, the coordinator runs a retirement checkpoint and reports a **Worktree cleanup** section. Exact paths are classified as `manual-retired`, `cleanup-ready`, `retained-dirty`, `retained-active`, `retained-blocked`, `app-cleanup-pending`, `app-auto-cleaned-restorable`, or `permanent-retained`. Dirty, unmerged, uncertain, or actively owned worktrees are retained and reported instead of being removed.

Archiving an App task is a separate authorized action. Codex may remove an archived App-managed worktree after preserving a restorable snapshot, so the coordinator verifies the resulting task and worktree state rather than assuming immediate deletion. Permanent worktrees are retained, and handoff is treated as migration rather than cleanup.

## Model and reasoning settings

Choose the execution surface before choosing model or reasoning settings. A full-history collaboration subagent inherits the parent task's current settings. A newly created implementation Codex App task is independent and uses risk-based adaptive model and reasoning selection by default; it does not inherit the coordinator task's transient settings or the last manually launched task's settings.

Classify risk from error consequences, authority boundaries, state persistence, rollback quality, and unresolved ambiguity rather than task size alone. Exact user pins, a higher-priority rule, or an explicit request to use configured defaults overrides adaptive routing. Each lane records its risk, primary difficulty, model, reasoning effort, and selection reason.

The default `risk-based-adaptive` profile uses Luna / medium for mechanical high-volume work, Terra / medium for narrow clear work, Terra / high for ordinary production implementation, Sol / medium when bounded interpretation is the main difficulty, and Sol / high for elevated cross-module, architectural, security, protocol, database, diagnostic, deployment, or final-integration work. Critical irreversible, tenant-isolation, data-loss, or weak-rollback work—and two failed review/fix cycles exposing design ambiguity—uses Sol / xhigh. Max and ultra are never selected automatically. In short: understanding favors Sol, multi-step execution favors Terra, throughput favors Luna, and risk sets the minimum effort.

For a user-reported Pro 20x account, record the `quality-biased-pro20x` variant without replacing every Terra lane with Sol. Sol / high is the recommended coordinator setting, with xhigh reserved for exceptional decision points and medium appropriate for sustained deterministic closure. The coordinator configures new App tasks automatically, but it cannot change its own current setting; it recommends a user-applied switch at a meaningful phase boundary when needed.

For progress tracking, the coordinator waits directly on up to eight ready targets and preserves event cursors. The implementation task remains the authoritative self-notifier. A separate listener is created only when the user explicitly asks for that user-visible task; it is a best-effort, read-only observer and never becomes notification, acceptance, merge, or cleanup authority. Use `read_thread` only when transcript or diagnostic detail is required, and do not report unchanged snapshots.

## Safety model

- Preserve the user's Git identity and repository rules.
- Keep secrets and credentials out of prompts, repository files, logs, and review descriptions.
- Treat branches and PRs or MRs as durable ownership records; thread IDs are runtime handles only.
- Record separate authorization for task creation, branch push, review creation, merge, deployment, base-checkout movement, task archive, branch deletion, and manual worktree removal.
- Report remaining worktrees after every merge; never make cleanup invisible.

## License

[MIT](LICENSE)
