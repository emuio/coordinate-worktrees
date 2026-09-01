---
name: coordinate-worktrees
description: Coordinate explicitly requested multi-lane Codex App delivery across isolated Git worktrees and separate branches, with independent pull or merge requests when remote review is authorized. Use when multiple user-visible implementation tasks must remain resumable and separately owned through integration and retirement; do not use for a single implementation, routine read-only analysis, or ordinary subagent delegation.
---

# Coordinate Worktrees

Operate one coordinator over several isolated delivery lanes. Keep durable ownership in branches, commits, and pull or merge requests; treat task and thread IDs as runtime handles.

## Route the work

Choose the execution surface before dispatching:

| Work | Surface | Git ownership |
| --- | --- | --- |
| Read-only investigation, mapping, or independent review | Collaboration subagent | None; shared filesystem |
| Explicitly requested, persistent multi-lane implementation | Codex App tasks in native worktrees | One branch per lane; remote review only when authorized |
| Tightly coupled edits to the same files or mutable state | One lane, sequentially | One owner |

Use collaboration subagents only for independent work that cannot create shared-filesystem edit conflicts. Do not create a user-visible App task unless the user explicitly requested a new task or a multi-task delivery. That authorization covers task creation only; it does not authorize push, review creation, merge, deployment, archive, branch deletion, or worktree removal.

## Record action authority

Classify the delivery before changing state:

| Mode | Allowed by default |
| --- | --- |
| `plan-only` | Read-only analysis, partitioning, and a proposed ledger |
| `local-delivery` | Explicitly requested App tasks, isolated worktrees, local branches, commits, and tests |
| `branch-delivery` | `local-delivery` plus an authorized branch push without creating a review |
| `review-delivery` | `branch-delivery` plus Draft PR or MR creation when the user's request explicitly includes remote review delivery |

Record separate authority for `createTasks`, `createListener`, `pushBranches`, `openReviews`, `merge`, `deploy`, `syncBaseCheckout`, `archiveTasks`, `deleteBranches`, and `removeManualWorktrees`, including its source. `createTasks` covers implementation tasks only; the optional observer has its own `createListener` authority. Treat unspecified authority as `pending`. Never put an unauthorized action in a lane's required brief. Remote writes, merge, deployment, base-checkout movement, archive, branch deletion, and worktree removal require explicit current authorization or a previously recorded delegation that clearly covers that action.

## Establish the control plane and ledger

A coordinator is the task registered as the control plane for one repository and delivery graph; it is not a hidden Codex task type. Use one coordinator per delivery graph unless release authority is genuinely independent. The coordinator owns partitioning, the ledger, steering, acceptance, merge decisions, authorized deployment, base synchronization, and lane retirement. It does not patch a delegated lane unless ownership is explicitly transferred with a recorded reason and scope.

Before dispatching or resuming lanes, read [the delivery ledger schema](references/delivery-ledger.md). Record a `ledgerLocation`; default to a complete checkpoint in the coordinator task unless the user authorizes a repository or external state file. Project association and searchable titles aid discovery, but the ledger, branch, and PR or MR remain the ownership record.

When new user messages arrive while commitments remain active, follow [the coordinator message and commitment protocol](references/coordinator-control-plane.md).

When coordinator ownership moves to another task, use that same protocol to import every non-retired lane, preserve prior event receipts and release records, update the route for nonterminal targets, and reconcile terminal targets. A handoff is incomplete while any source lane is absent or still routes new notifications only to the old coordinator.

## Choose worktree placement

- Prefer Codex-managed worktrees for persistent implementation tasks. Do not manually remove an App-managed worktree.
- Collaboration subagents share the coordinator filesystem and must not create manual worktrees.
- Use a manual worktree only when the user explicitly requests one or native worktree task tooling is unavailable and the user authorizes the fallback. Put it below one dedicated coordinator-owned root, never beside the primary checkout or inside the App-managed root.
- Record `placementOwner`, absolute path, `worktreeKind` (`codex-managed`, `permanent`, or `coordinator-manual`), and `retirementPolicy` before implementation.

## Resolve the final base

Define one `finalBaseBranch`, `baseRemote`, absolute `baseCheckout`, and `baseSyncOwner`. Resolve the final base from an explicit instruction, an existing umbrella review target, or the base remote's symbolic default, in that order. Stop when these conflict; never assume `main`, `master`, `develop`, or another conventional name.

Use only a registered coordinator-owned or explicitly selected base checkout. Before fixing lane base SHAs, fetch the base remote and verify the worktree mapping and clean state. Move that checkout only under `syncBaseCheckout` authority and only by fast-forward; otherwise record a pending or blocked result. Child lanes must not operate on the base checkout. Before any base synchronization or retirement action, read and follow [the base synchronization and retirement protocol](references/base-sync-and-retirement.md).

## Choose model and reasoning settings

- A full-history collaboration subagent inherits the parent task's current model and reasoning effort.
- A new implementation App task uses risk-based adaptive model and reasoning selection by default; it does not inherit the coordinator's transient settings or the last manually launched task's settings.
- Exact user-selected pins, a higher-priority applicable instruction, or an explicit request to use configured defaults overrides adaptive routing. This selection rule changes task configuration only; it does not authorize task creation or any Git, review, deployment, or retirement action.
- Validate every selected override against the current task-creation capability. Use the closest supported setting only when it preserves the same risk floor; otherwise report the mismatch and obtain a supported choice instead of silently downgrading.

Before selecting a setting, classify risk from the consequence of an error, authority boundaries, state persistence, rollback quality, and unresolved ambiguity. Task size or a vague impression of difficulty is not enough. Use `routine`, `elevated`, or `critical`; the risk level is an effort floor, while the primary difficulty selects the model family.

Use the `risk-based-adaptive` profile by default. When the user reports Pro 20x, record that context and use its quality-biased variant, `quality-biased-pro20x`. It deliberately keeps Terra instead of replacing every lane with Sol:

| Risk and primary difficulty | New implementation task |
| --- | --- |
| Routine, repetitive, mechanical, or high-volume | Luna / medium |
| Routine, narrow, clear, and low-risk implementation | Terra / medium |
| Ordinary production implementation with multi-step verification | Terra / high |
| Routine, bounded work whose main difficulty is interpretation or judgment | Sol / medium |
| Elevated: cross-service contracts, authentication or authorization, persistent-data changes, concurrency or idempotency, deployment or rollback, real-service writes, material ambiguity, or final integration review | Sol / high |
| Critical: irreversible production mutation, security-authority or tenant-isolation change, credible data-loss risk, coordinated multi-repository release with weak rollback, or two failed review/fix cycles exposing unresolved design ambiguity | Sol / xhigh |

Choose the family from the source of difficulty: understanding and judgment favor Sol, multi-step implementation and verification favor Terra, and throughput favors Luna. Choose reasoning effort from ambiguity and risk. An elevated task must not run below high and a critical task must not run below xhigh merely because its edits are mechanical. Do not automatically select max or ultra; they require an exact user choice or higher-priority policy. Pro 20x permits a quality bias but is not unlimited and does not remove latency, so do not blanket-upgrade all lanes to Sol or xhigh. Reassess before a follow-up when scope or evidence crosses a risk boundary and at the transition from design to deterministic closure; do not interrupt an in-progress task only to reconfigure it. Record the profile, risk, difficulty source, selected model, effort, and one-sentence rationale per lane.

For the coordinator task itself, `quality-biased-pro20x` recommends Sol / high as the normal coordination setting, Sol / xhigh only for exceptional architecture, security, release, or non-converging decisions, and medium for sustained deterministic closure. The coordinator cannot change its own current model or reasoning setting: at a meaningful phase boundary it may recommend that the user switch, without interrupting active implementation merely to downgrade. The profile covers implementation lanes only; an optional listener still uses configured defaults unless the user separately chooses its settings.

## Establish the delivery graph

1. Read repository instructions, the approved design or spec, and the implementation plan.
2. Identify the real repository root, dirty state, remote, final base, registered base checkout, and fixed base SHA. Preserve unrelated user changes.
3. Choose the smallest useful set of lanes. Partition by dependency and file ownership; keep overlapping files in one lane or define an explicit merge order.
4. Create or select an integration branch. Open a Draft umbrella PR or MR only when both `pushBranches` and `openReviews` are authorized. Record `local-only` when neither remote branch delivery nor review was requested, and `remote-branch-only` when push is authorized but review was explicitly declined. Use `remote-review-pending` only when remote review is intended but one or both required authorities remain pending or denied.
5. Populate the ledger with authority, dependencies, scopes, bases, verification commands, placement, task setup state, Git state, notification state, release batches, and retirement policy.

Creating a remote repository or changing its visibility always requires explicit authorization.

## Dispatch a persistent lane

1. Resolve current thread capabilities by semantic operation (`list_projects`, `create_thread`, `list_threads`, `wait_threads`, `read_thread`, and `send_message_to_thread`) instead of assuming a fixed namespace or error string. If a required capability is unavailable after discovery, report the boundary.
2. Call `list_projects` from the current entry point. Record the selected project's `projectId`, `projectKind`, `isGitRepository`, path when present, and `hostId` when present. Do not route a ChatGPT project through a Codex worktree flow.
3. Create a task only under recorded `createTasks` authority. For a Git project, default to a native `worktree`; use the saved project directly only when the user explicitly requested that environment. For a non-Git project use `local`. Start a Git worktree from an existing integration or parent branch; never invent a missing starting ref.
4. Select and pass model and reasoning overrides from the default adaptive profile, exact user pins, or a higher-priority applicable instruction. Leave them unset only when the user explicitly requests configured defaults. Pass the complete lane brief as the initial `create_thread` prompt, set the title in that call when supported, and leave the task unpinned unless the user requested pinning.
5. Include in the brief:
   - independent-main-task role, exact scope, owned files, and exclusions;
   - base branch and SHA, required source paths, tests, and known baseline failures;
   - routing profile, risk classification, primary difficulty, selected model and reasoning effort, and the evidence for that selection;
   - required named branch and repository commit identity and message rules;
   - exactly which local and remote actions are authorized, with unauthorized actions prohibited;
   - no self-merge; the coordinator retains acceptance and merge authority;
   - `notificationOwner=target-self`, the coordinator's exact `threadId` and `hostId`, and a coordinator-assigned `notificationCycleId` that is unique to the initial, review-fix, or coordinator-handoff cycle;
   - one completion or `needs_attention` notification that echoes `notificationCycleId`, task identity, status, and a stable `noticeId` unique within that cycle and reused only for a transport retry, plus a cursor only when available, with at most one retry and no false delivery or cursor claim;
   - final report fields: task handle, worktree, branch, HEAD, review URL when authorized, tests, and blockers.
6. Classify the creation result:
   - `ready`: a real `threadId` and `hostId` are available;
   - `setup-pending`: only a `clientThreadId` or equivalent provisioning handle is available;
   - `creation-failed`: no usable task was created.
   Never pass a provisioning handle to an operation that requires `threadId`, send follow-up work to it, probe it, or claim the lane is ready. Resolve the eventual real task only through a product-provided association in current App task state; never match by title or recency alone. If no reliable association is exposed, keep the lane `setup-pending` and report that boundary.
7. Codex-managed worktrees can begin at detached HEAD. Require the owning task to create and verify its named branch before its first edit or commit.

Completion criterion: every dispatched lane is either honestly `setup-pending`, or is visible with a real task handle, isolated worktree, named branch, bounded scope, verification command, notification route, and explicit action authority.

## Coordinate without taking ownership away

- Call event-driven `wait_threads` for one to eight ready targets only when the next committed coordinator action depends on a target event and no other authorized coordinator work can advance. Preserve each cursor. A timeout is not completion; do not turn unsupported waiting into polling or repeated `read_thread` calls.
- Treat direct wait results, target self-notifications, and optional observer notices as at-least-once inputs. Before acting, correlate them to one durable event receipt using exact target `threadId`, target `hostId`, `notificationCycleId`, status, event cursor, and stable `noticeId` where those fields exist. Keep completed-cycle receipts through lane retirement; never clear the old receipt when a review-fix cycle gets a new `notificationCycleId`. An input that cannot be correlated is only a wakeup until current task state and cycle evidence resolve it; status alone is never enough.
- Follow the event-receipt and effect-recovery rules in [the delivery ledger schema](references/delivery-ledger.md). Duplicate inputs may add delivery evidence or a previously missing cursor, but they do not directly repeat acceptance, user reporting, merge, or another mutation. If an earlier effect is still pending after interruption, reconcile destination state before retrying instead of assuming it ran or blindly replaying it.
- Use `read_thread` only for detailed transcript or diagnostic evidence and `list_threads` only to relocate or resolve a handle.
- Send corrections when scope, branch, tests, notification routing, or action authority drifts. Let the owning task implement its fixes.
- Before a follow-up starts a new target turn after a terminal event, assign and record a new `notificationCycleId`, preserve all prior event receipts, set the new cycle's start cursor when reliably known, and include the new ID in the follow-up. If the boundary cursor is unknown, keep target-self but do not claim cursor-based waiting or observer rearm for that cycle.
- Wait at meaningful checkpoints and report changed lane state and review decisions, not routine internal chatter.
- `target-self` remains the authoritative notification route. Self-notification is best-effort; coordinator-side task state remains the verification source.

Do not create a dedicated listener because tasks are numerous, long-running, or because the coordinator wants convenience. Only when the user explicitly requests a separate user-visible listener task, read and follow [the optional task-listener protocol](references/task-listener.md). A listener is an observer, never the notification owner or acceptance authority.

## Review and integrate

1. Verify each child review's source and target branches, fixed base, author and committer identity, diff scope, conflicts, Draft state, and current checks. Include `git diff --check`.
2. Review both repository standards and required behavior. Adjudicate findings and return actionable blockers to the same owning task; do not patch its worktree without an ownership transfer.
3. Re-run relevant checks after fixes. A lane's self-review does not replace coordinator acceptance.
4. Merge child reviews into integration only when blockers are closed and merge authority covers that action. Re-check remaining diffs after each merge.
5. Start dependent lanes from the updated integration branch. Run full repository gates and required smoke tests on the integrated result.
6. Review the umbrella change against the authoritative spec and final base. If final merge is not authorized, report merge readiness and stop.
7. After every authorized merge into `finalBaseBranch`, run the base synchronization checkpoint. After every merged or explicitly abandoned lane, run the retirement checkpoint. Both are defined in [the base synchronization and retirement protocol](references/base-sync-and-retirement.md).

## Reconcile release and retirement

Before any authorized deployment, create or select one release batch in the ledger and scan the complete delivery graph, not only the reviews merged in the current turn. Every completed lane whose result is not already covered by a verified earlier release must have exactly one current `releaseDisposition`: `include`, `defer`, `blocked`, or `not-applicable`. An included or deferred lane must identify the coordinator-accepted HEAD; an included lane must also identify the integrated commit. Record a reason for every deferred, blocked, or not-applicable decision.

Serialize the complete current ledger to JSON and run [`scripts/validate_ledger.py`](scripts/validate_ledger.py) with `--phase pre-deploy`. Use an ephemeral file or standard input when repository or external ledger writes are not authorized. A missing disposition, missing acceptance or integration evidence, stale coordinator notification route, malformed ledger, or nonzero validator result blocks deployment. The validator is read-only and never grants `deploy` authority.

After deployment, prove the exact deployed target and immutable release identifier, then verify each included lane through its `acceptedHead`, `integratedCommit`, `deployedTarget`, `deployedRelease`, and deployment evidence. Run every included lane's retirement checkpoint, including lanes merged in an earlier turn, and run the validator again with `--phase post-deploy` before the final report. A deployed lane must have a verified retirement disposition or a precise blocker. `retirementPolicy` is a coordinator instruction, not an App automation trigger: archive requires `archiveTasks` authority, an explicit archive call, and a read-back classification of archived or `app-cleanup-pending`.

## Guardrails

- Preserve the user's Git identity and repository-specific commit rules; never add AI or bot attribution unless requested.
- Keep secrets and credentials out of prompts, repository files, logs, and review descriptions.
- Never infer durable ownership from a title, sidebar order, session, or thread handle alone.
- Separate read-only observation from task creation and from external mutations.
- Serialize merges and base synchronization through the coordinator while implementation lanes run in parallel.
- Never trade cleanup convenience for recoverability. Retain uncertain work and report the exact blocker.
