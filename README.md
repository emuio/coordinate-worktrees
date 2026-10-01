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

| Work | Execution surface | Ownership and isolation |
| --- | --- | --- |
| One-time investigation, message/evidence check, or independent review | Collaboration subagent | Read-only shared filesystem |
| One-time test, documentation, or bounded edit | Scoped collaboration subagent | Authorized paths and exclusive owned files |
| Sustained implementation with independent commits and delivery | Explicitly requested or already authorized Codex App task | Independent worktree and branch |
| Integration across stages or days, with separate recovery or handoff | Explicitly requested or already authorized persistent App task | Read-only work may be projectless; no branch needed for duration alone |
| Explicitly requested external-message intake or routing, such as DWS | Dedicated App task and existing or authorized event backend | Separate task, backend, and message-routing authority |
| Coupled edits to the same files or state | One sequential owner | Reuse the existing owner |

Within an authorized coordination delivery, reuse the current owner first, then choose the surface by whether the assignment has a bounded result or needs ongoing independent ownership. Record the choice, reason, scope, owned paths, and completion condition or checkpoint. Select model and reasoning separately; this routing does not expand the skill to ordinary standalone subagent work. External-message intake is distinct from the optional child-task status observer.

The coordinator owns the delivery graph, integration state, review decisions, and any authorized final merge. Each implementation lane owns its branch, commits, checks, and review fixes, but does not merge itself.

Keep the coordinator available by delegating lengthy implementation, tests, integration, and external waiting within existing authority. Retain requirements, dispatch, evidence review, acceptance, and necessary short or serialized checks in the coordinator. Preserve each unfinished item's owner and checkpoint, process correlated notices at meaningful checkpoints, and use bounded event-driven waits when no other authorized work can advance. See [the coordinator protocol](skills/coordinate-worktrees/references/coordinator-control-plane.md).

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

The default `sol-6.1-first-adaptive` profile uses GPT-6.1 Sol (`gpt-6.1-sol`) / medium for bounded implementation, fixes, routine tests, and documentation; GPT-6.1 Sol / high for complex design, diagnosis, integration judgment, or elevated risk; and GPT-6 Astra (`gpt-6-astra`) / xhigh for critical security/data risk, weak rollback, or persistent design ambiguity. Assess difficulty separately from risk: domain keywords and file count alone do not imply critical work. Never automatically select max or ultra.

The coordinator recommendation is GPT-6.1 Sol / high as a stable setting, with a user-applied switch to Astra / xhigh for concrete critical decisions or sustained non-convergence. Suggest a change to medium only for a substantial deterministic phase, not brief steps or tool waits. Do not assume App UI changes preserve prompt caching. User-reported Pro 20x is account context, not a separate profile.

Verify destination-host support and record the exact model ID. If GPT-6.1 Sol is unavailable, use Astra at the required effort; if Astra is unavailable for critical work, use GPT-6.1 Sol / xhigh. Other choices require explicit user choice, higher-priority policy, or requested economy/high throughput. Keep existing lane settings and provenance on resume, applying the default to newly dispatched lanes. An optional listener retains configured defaults. See [the authoritative routing rules](skills/coordinate-worktrees/SKILL.md#choose-model-and-reasoning-settings).

Evaluate the profile during ordinary delivery using observed quality, review rework, and material delays in existing lane reports. Adjust the affected task class from feedback; this default does not claim a validated performance improvement.

For progress tracking, the coordinator waits directly on up to eight ready targets and preserves event cursors. The implementation task remains the authoritative self-notifier. A separate listener is created only when the user explicitly asks for that user-visible task; it is a best-effort, read-only observer and never becomes notification, acceptance, merge, or cleanup authority. Use `read_thread` only when transcript or diagnostic detail is required, and do not report unchanged snapshots.

## Safety model

- Preserve the user's Git identity and repository rules.
- Keep secrets and credentials out of prompts, repository files, logs, and review descriptions.
- Treat branches and PRs or MRs as durable ownership records; thread IDs are runtime handles only.
- Record separate authorization for task creation, branch push, review creation, merge, deployment, base-checkout movement, task archive, branch deletion, and manual worktree removal.
- Report remaining worktrees after every merge; never make cleanup invisible.

## License

[MIT](LICENSE)
