---
name: coordinate-worktrees
description: Coordinate persistent Codex App tasks across isolated Git worktrees, parallel or stacked merge requests or pull requests, progress steering, review handbacks, coordinator-owned merge decisions, base checkout synchronization, and safe lane retirement. Use when delivery must remain user-visible, resumable, and independently reviewable, when deciding whether work belongs in a short-lived subagent or persistent worktree task, or when safely integrating and cleaning up completed worktrees and branches.
---

# Coordinate Worktrees

Operate as one coordinator task over several isolated delivery lanes. Keep task identity durable in the branch, commit, and MR; treat Codex thread IDs as runtime handles.

## Route the work

Choose the execution surface before dispatching:

| Work | Surface | Git ownership |
| --- | --- | --- |
| Read-only investigation, mapping, or independent review | Collaboration subagent | None; shared filesystem |
| Long-running implementation that needs commits or an MR | Codex App task in a native worktree | Dedicated branch and MR |
| Tightly coupled edits to the same files or state | One lane, sequentially | One owner |

Use a subagent only when shared filesystem access cannot create edit conflicts. Use a Codex App task when the result must remain visible, resumable, independently reviewable, or owned through an MR.

Treat an explicit request to dispatch work to other user-visible tasks as authorization to create those App tasks. If that authorization is absent, ask before calling `codex_app__create_thread`.

## Choose worktree placement and ownership

- Prefer a Codex App task's native worktree for persistent, user-visible implementation. Its physical path is App-managed (commonly below `~/.codex/worktrees/`, but do not depend on that layout), and the coordinator must not manually remove it.
- Collaboration subagents share the coordinator's filesystem. They do not create an isolated worktree and must not run manual `git worktree add` commands.
- Use a manual worktree only as an explicit fallback when native App worktree tooling is unavailable or the user requests a coordinator-owned manual lane. Put it under one dedicated root outside the repository's parent directory, such as `${CODEX_HOME:-$HOME/.codex}/manual-worktrees/<repository>/<lane>`.
- Do not scatter manual worktrees beside the primary checkout (for example, many sibling `project-*` directories), and do not place coordinator-owned manual worktrees inside the App-managed worktree root.
- Record `placementOwner` (`codex-app` or `coordinator-manual`), absolute path, and `retirementPolicy` in the lane ledger. Use one of: `report-only` (safe default), `retire-clean-manual-after-merge`, or `archive-app-task-after-merge`.

Completion criterion: every persistent lane has an explicit placement owner, a deterministic path policy, and a declared retirement policy before implementation begins.

## Resolve and maintain the final base

- Define one `finalBaseBranch`, one `baseRemote`, and one absolute `baseCheckout` for the delivery graph. The base checkout is a clean coordination and synchronization surface, not an implementation lane.
- Resolve `finalBaseBranch` in this order: an explicit user or repository instruction; the target of an existing umbrella MR or PR; the base remote's symbolic default branch. If these sources conflict or none is reliable, stop and ask instead of assuming `master`, `main`, `develop`, or another conventional name.
- Record how the final base was resolved, its remote-tracking ref, the base checkout's branch and HEAD, and one coordinator as `baseSyncOwner`. Child lanes must not switch, update, or otherwise operate on the base checkout.
- Before fixing a base SHA or dispatching a lane, fetch the base remote, verify the exact worktree mapping and clean status, and update the base checkout only when it is already on `finalBaseBranch` and its HEAD is an ancestor of `<baseRemote>/<finalBaseBranch>`. Use a fast-forward-only update and verify that both HEADs match afterward.
- Serialize all base checkout synchronization through `baseSyncOwner`. Parallel implementation is allowed, but child merges and base synchronization remain ordered coordinator operations.
- Classify synchronization as `base-sync-current`, `base-sync-pending`, or `base-sync-blocked`. Use `base-sync-blocked` when the default or final base is ambiguous, the checkout is missing, dirty, active elsewhere, on another branch, occupied inconsistently in another worktree, diverged, or cannot fast-forward.
- A blocked synchronization is fail-closed: do not stash, discard, reset, force-switch, create a conflict-producing merge, rename a branch, or repurpose a checkout without explicit authorization. Preserve the observed state and report the exact blocker and safe next action.

Completion criterion: the delivery graph has one dynamically resolved final base, a current or explicitly blocked base checkout, one synchronization owner, and a fixed base SHA obtained after the synchronization checkpoint.

## Choose model and reasoning settings

Choose the execution surface first; model and reasoning settings are a secondary decision. Do not present automatic difficulty-based model routing as a Codex default.

| Surface | Default behavior | Coordinator rule |
| --- | --- | --- |
| Full-history collaboration subagent | Inherits the parent task's current model and reasoning effort | Keep inheritance unless the user, applicable instructions, or the selected skill explicitly requires an override and the spawn form permits it |
| New Codex App task | Uses configured defaults when model and reasoning overrides are omitted; it does not inherit the coordinator task's transient settings | Do not silently pin or change settings; when the choice materially affects the work, state the expected default and obtain an explicit choice before overriding it |

Record the model, reasoning effort, and their source when known: inherited, configured default, or explicitly pinned. Do not add project or global custom agents merely to route persistent App tasks; those tasks have their own configuration path.

## Establish the delivery graph

1. Read repository instructions, the approved design/spec, and the implementation plan.
2. Identify the real repository root, current dirty state, remote, dynamically resolved final base branch, base checkout, and fixed base SHA. Run the base synchronization checkpoint before fixing that SHA. Preserve unrelated user changes.
3. Partition work by dependency and file ownership. Put overlapping files in one lane or define a merge order; do not rely on agents to reconcile concurrent shared edits.
4. Create or select an integration branch. For a multi-MR delivery, open a Draft umbrella MR from integration to the final base before implementation begins.
5. Record the delivery-level final base, resolution source, base checkout, base synchronization owner and status. Record for every lane: scope, dependencies, execution surface, model and reasoning source when known, App thread ID, worktree, placement owner, retirement policy, branch, base SHA, MR target, MR URL, HEAD, tests, and status.

Creating a remote repository or changing repository visibility is external state. Do it only when the user already authorized that outcome or after confirmation.

Completion criterion: every implementation unit has one owner, an explicit base, a non-overlapping scope or merge order, and a declared verification command.

## Dispatch a persistent lane

1. Resolve the saved project with `codex_app__list_projects`.
2. Create the task with `codex_app__create_thread`, target the project, choose the native `worktree` environment, and set `startingState.branchName` to the existing integration branch or required parent branch. Prefer the App's native worktree over manual `git worktree` commands.
   Unless the user explicitly selected a model or reasoning level, leave those overrides unset so the task uses configured defaults.
3. Give the task a searchable title. Leave it unpinned unless the user explicitly requests pinning; do not use sidebar order as coordination state.
4. Send a self-contained brief containing:
   - role: independent main task, not a one-shot worker;
   - exact scope, owned files/modules, and excluded scope;
   - base branch and base SHA;
   - required design, plan, and repository instruction paths;
   - required tests and any known baseline failures;
   - dedicated `codex/` branch name and target integration branch;
   - commit identity and message rules from the repository;
   - requirement to commit, verify, push, and open a Draft MR;
   - prohibition on self-merging; the coordinator owns review and merge;
   - required final report: worktree, branch, HEAD, MR URL, tests, and blockers.
5. Codex App worktrees can begin at detached HEAD. Require the lane to create and verify its named branch before its first edit or commit.

If native App thread/worktree tools are unavailable, report that boundary. Do not silently replace a requested persistent lane with a hidden subagent or an unmanaged manual worktree.

Completion criterion: the task is visible in Codex App, attached to its own worktree and named branch, and its brief names both the MR target and the no-self-merge rule.

## Coordinate without taking ownership away

- Follow progress with bounded `wait_threads` calls. Use one call for one to eight targets, pass each target's latest cursor, and use `timeoutMs: 0` for an immediate compact snapshot.
- Use `read_thread` only when the full transcript or diagnostic detail is required; use `list_threads` only to relocate a handle.
- Send corrections with `codex_app__send_message_to_thread` when scope, branch, test evidence, or ownership drifts.
- Send baseline failures to every affected lane so workers separate pre-existing failures from regressions.
- Let the owning task implement its fixes. Do not patch its worktree from the coordinator unless ownership is explicitly transferred.
- Wait at meaningful checkpoints: branch creation, first vertical slice, gate completion, MR creation, and requested-fix completion. Do not narrate unchanged snapshots or answer approval and user-input requests on behalf of the user.
- Keep the user informed of lane state and review decisions, not raw internal chatter.

For several or long-running App tasks, or when the user explicitly requests low-cost monitoring, the coordinator may create or reuse a projectless, independent, read-only App task as an optional listener. Do not require one for a single short task. Before dispatching or reusing a listener, read and follow [the task-listener protocol and reusable prompt](references/task-listener.md); record its observer handle, settings source, and targets in the coordinator ledger while keeping acceptance and delivery authority with the coordinator.

Completion criterion: each active lane has one current owner and the ledger matches its actual branch, HEAD, and MR state.

## Review each child MR

1. Verify source branch, target branch, fixed base SHA, author/committer identity, diff scope, conflicts, and Draft state.
2. Re-run risk-proportionate checks from the lane's worktree or fetched branch. Include `git diff --check`.
3. If the `code-review` skill is available, run its two axes from the fixed base:
   - Standards: repository rules, architecture, tests, security, and maintainability.
   - Spec: required behavior, missing behavior, wrong behavior, and extra scope.
4. Adjudicate findings yourself. Return actionable blockers to the same owning App task, with file/line evidence and required acceptance tests.
5. Re-run the relevant checks and both review axes after fixes. A worker's self-review does not replace coordinator review.
6. Merge only when blockers are closed and the MR still targets the intended integration branch.

Completion criterion: the coordinator has current test evidence, both review axes are clean or explicitly adjudicated, and the merge decision is recorded.

## Integrate in dependency order

1. Merge independent child MRs into integration in the declared order.
2. After each merge, verify integration HEAD and re-check remaining child diffs for target drift or conflicts.
3. Create dependent integration tasks only from the updated integration branch, never from the original base.
4. Run the full repository gates and required manual smoke tests on the integrated result.
5. Review the umbrella MR against the authoritative spec and the final base. Merge it only when the user authorized the coordinator to decide; otherwise report readiness and wait.
6. Immediately run the post-MR retirement checkpoint below after every merge. Retire a lane only after its work is merged or deliberately abandoned and all safety checks pass.
7. After an MR or PR into `finalBaseBranch` is confirmed merged, run the post-integration base synchronization checkpoint below. A child merge into an integration branch must not update the final base checkout.

Completion criterion: the final branch contains only reviewed child work, full gates reflect the integrated tree, manual checks are honestly reported, no required MR or task remains unresolved, and the base checkout is current or explicitly blocked.

## Run a post-integration base synchronization checkpoint

Run this checkpoint only after the final MR or PR target is `finalBaseBranch` and its merged state is refreshed from the remote. Run it again before the coordinator's final response:

1. Revalidate the configured remote default. If it no longer agrees with the recorded final base and no explicit instruction overrides it, mark `base-sync-blocked` and re-plan instead of silently switching branches.
2. Refresh the exact `git worktree list --porcelain` mapping, the base checkout's current branch and HEAD, its owning task or process state when relevant, and `git status --porcelain`.
3. Let only `baseSyncOwner` perform the synchronization. Do not run concurrent fetch, switch, merge, or branch operations against the base checkout from child lanes or other coordinators.
4. Fetch `baseRemote`, confirm that the local base HEAD is an ancestor of `<baseRemote>/<finalBaseBranch>`, then fast-forward with `git -C <baseCheckout> merge --ff-only <baseRemote>/<finalBaseBranch>`.
5. Verify that the base checkout HEAD exactly matches the refreshed remote-tracking ref. Otherwise mark `base-sync-blocked`; do not fall back to a normal merge, rebase, reset, or force operation.
6. Always report a `Base checkout sync` section with the absolute path, remote, final base branch, local and remote HEADs, classification, whether an update occurred, and any blocker or next action.

If the final MR or PR is ready but not merged because authorization is pending, report `base-sync-pending`; do not move the base checkout to an unmerged integration result.

Completion criterion: synchronization is serialized, conflict-free by construction, and reported as exactly current, pending, or blocked without modifying unrelated or unrecoverable state.

## Run a post-MR retirement checkpoint

Run this checkpoint after every merged or deliberately abandoned lane and again before the coordinator's final response:

1. Refresh the MR state and target containment; do not rely on a worker's earlier completion report.
2. Refresh the owning task state and the exact `git worktree list --porcelain` mapping.
3. Refresh `git status --porcelain` in the exact worktree and compare branch and HEAD with the ledger.
4. Classify the lane as exactly one of:
   - `retired`: authorized cleanup completed and the ledger was updated;
   - `cleanup-ready`: all safety checks pass, but cleanup still needs authorization or execution;
   - `retained-dirty`: uncommitted or untracked work is present;
   - `retained-active`: an owning task or another workflow still uses the lane;
   - `app-lifecycle-pending`: the App task is archived or complete, but its App-managed physical worktree remains under App ownership.
5. Always report a `Worktree cleanup` section to the user. Include each affected absolute path, classification, whether its branch was retained or removed, whether recovery refs or stashes exist, and the next action. Report the section even when no path was deleted.

Never silently leave completed manual lanes scattered on disk. Never silently delete them either: the checkpoint makes both the cleanup decision and any remaining responsibility visible.

Completion criterion: after every merge, the user can see which exact worktrees were removed, which remain, why they remain, and how any abandoned changes can be recovered.

## Retire completed lanes safely

1. Resolve the lane from the ledger. Record its owner, App task, absolute worktree path, branch, HEAD, MR, target branch, and whether the worktree is App-managed or manual.
2. Verify retirement with read-only evidence:
   - the MR is merged, or abandonment is explicit and its HEAD is preserved on a recoverable remote ref;
   - the target branch contains the intended HEAD or merge commit;
   - the owning task is no longer running;
   - `git worktree list --porcelain` maps the exact path to the expected branch and HEAD;
   - `git -C <absolute-worktree-path> status --porcelain` is empty.
3. Stop and report instead of cleaning when the path, branch, or HEAD differs from the ledger; the worktree is dirty; the branch is unmerged or unpushed; another task owns it; or abandonment would discard unrecoverable work.
4. For an App-managed worktree, archive the task after verification when retirement is authorized. Do not change its pin state unless the user explicitly requests it. Do not assume archiving removes the physical worktree, and do not manually remove a worktree still owned by Codex App. Use an App-provided lifecycle or handoff operation when available; otherwise leave physical cleanup to the App and record that state.
5. For a coordinator-owned manual worktree, remove only the verified absolute path with `git worktree remove <absolute-worktree-path>`, then run `git worktree prune`. Never use a glob, unresolved variable, broad parent directory, `rm -rf`, or `git worktree remove --force` as the default cleanup path.
6. Delete a local lane branch only after its merged state is verified. Delete a remote branch only when repository policy or explicit user authorization permits it. Retire an integration branch only after the umbrella MR is merged and no open child MR still targets it.
7. Mark the ledger entry with the post-MR classification. When retired, record the merge or preservation ref, task archive state, worktree disposition, branch disposition, and cleanup timestamp.

Completion criterion: all retired work remains recoverable from the merged target or recorded remote ref, no dirty or actively owned worktree was removed, and the ledger matches the remaining App tasks, worktrees, and branches.

## Guardrails

- Preserve the user's Git identity; never add AI or bot attribution unless requested.
- Keep commits small and repository-compliant.
- Keep secrets and credentials out of prompts, repository files, logs, and MR descriptions.
- Treat branch/MR ownership as the durable control plane; never infer durable ownership from a session or thread handle alone.
- Separate read-only observation from actions that push, merge, close, or mutate external systems.
- Never hardcode a conventional default branch name. Resolve and record the final base for each delivery graph, and fail closed if it becomes ambiguous or changes unexpectedly.
- Keep parallelism in implementation lanes; serialize merges and base checkout synchronization through the coordinator. Fast-forward-only base synchronization must fail instead of producing conflicts.
- Never trade cleanup convenience for recoverability; leave uncertain lanes in place and report the exact blocking evidence.
