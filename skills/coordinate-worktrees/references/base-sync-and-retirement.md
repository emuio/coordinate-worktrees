# Base Synchronization and Lane Retirement

Read this reference before modifying the registered base checkout, deploying a release batch, archiving an App task, deleting a branch, or removing a manual worktree.

## Resolve and prepare the final base

1. Resolve `finalBaseBranch` from an explicit instruction, an existing umbrella review target, or the base remote's symbolic default, in that order. Stop if these disagree or none is reliable.
2. Record `baseRemote`, its remote-tracking ref, the absolute registered `baseCheckout`, its branch and HEAD, and one `baseSyncOwner`.
3. Fetch the base remote and refresh the worktree mapping and clean status before fixing lane base SHAs.
4. Update only the registered coordinator-owned or explicitly selected base checkout, only when its HEAD is an ancestor of the refreshed remote-tracking ref, and only by fast-forward.
5. Classify the result as `base-sync-current`, `base-sync-pending`, or `base-sync-blocked`.

Use `base-sync-blocked` when the final base is ambiguous, the checkout is missing, dirty, owned by an active task, unexpectedly on another branch, occupied inconsistently in another worktree, diverged, or unable to fast-forward. Fail closed: do not stash, reset, force-switch, rebase, create a conflict-producing merge, rename a branch, or repurpose a checkout to make synchronization succeed.

Moving or switching the registered base checkout requires `syncBaseCheckout` authority. Without it, inspection and classification may proceed, but leave the checkout unchanged and report `base-sync-pending` with the exact proposed fast-forward or controlled return.

## Run the post-integration checkpoint

Run this checkpoint after every confirmed merge into `finalBaseBranch` and again before the coordinator's final delivery report:

1. Refresh the merged review state and the base remote's symbolic default.
2. Fetch `baseRemote` and refresh `<baseRemote>/<finalBaseBranch>`.
3. Refresh `git worktree list --porcelain`, the registered checkout's branch and HEAD, its current owner or task state when relevant, and `git status --porcelain`.
4. Let only `baseSyncOwner` act on the registered checkout.
5. If the checkout is already on `finalBaseBranch`, require it to be clean and its HEAD to be an ancestor of the refreshed remote-tracking ref.
6. If the checkout is already on `finalBaseBranch` and its HEAD equals the refreshed final-base ref, report `base-sync-current` without requiring mutation authority. Otherwise, when `syncBaseCheckout` is not authorized, leave it unchanged, report `base-sync-pending`, and stop the mutation path.
7. If it is on another branch and movement is authorized, return it to `finalBaseBranch` only when it is clean, coordinator-owned, inactive, unambiguously mapped, its HEAD is an ancestor of the refreshed final base, and the remote default still agrees. Otherwise leave it unchanged, mark `base-sync-blocked`, and stop the mutation path.
8. Fast-forward only with `git -C <baseCheckout> merge --ff-only <baseRemote>/<finalBaseBranch>`.
9. Verify the resulting HEAD exactly equals the refreshed remote-tracking ref. Never fall back to merge, rebase, reset, or force.

If the final review is ready but not authorized to merge, report `base-sync-pending` and do not move the base checkout to an unmerged result.

Always report a `Base checkout sync` section containing the absolute path, remote, final base, previous branch and HEAD, resulting branch and HEAD, classification, whether an update or controlled return occurred, and any blocker or next action.

## Classify worktree kind before retirement

Record exactly one:

- `codex-managed`: a disposable App-managed worktree associated with one task.
- `permanent`: a long-lived App worktree or project that is not automatically retired with one task.
- `coordinator-manual`: a manual worktree created and owned under explicit coordinator authority.

Do not infer kind or ownership from directory names alone.

## Run the retirement checkpoint

After every merged or explicitly abandoned lane, after every verified deployment, and before the final report:

1. Refresh review state and target containment. Do not rely on the lane's earlier report.
2. Refresh the owning task state and archive state when relevant.
3. Refresh the exact worktree mapping, path, branch, HEAD, and clean status when the worktree still exists.
4. Compare all evidence with the ledger and classify exactly one disposition:
   - `manual-retired`: authorized cleanup of a coordinator-manual worktree completed and the ledger was updated;
   - `cleanup-ready`: all safety checks pass, but authorized cleanup has not executed;
   - `retained-dirty`: tracked, untracked, staged, or unstaged work remains;
   - `retained-active`: an owning task or another workflow still uses the lane;
   - `retained-blocked`: cleanup is unsafe for another recorded reason, such as `unmerged`, `unpushed`, `ledger-mismatch`, `unknown-path`, or `unrecoverable-head`;
   - `app-cleanup-pending`: archive was authorized and requested for a Codex-managed task, but background cleanup is not yet verified;
   - `app-auto-cleaned-restorable`: the App removed a Codex-managed worktree after preserving its restorable snapshot;
   - `permanent-retained`: a permanent worktree remains intentionally under App or user ownership.
5. Report a `Worktree cleanup` section with each absolute path when one exists, classification, worktree kind, branch disposition, recovery ref or snapshot state, blocker, and next action. Report App-removed paths as historical paths rather than fabricating a current mapping.

After a deployment, apply this checkpoint to every included lane in the active release batch, not only lanes merged during the current coordinator turn. Before reporting the release complete, verify that each included lane's accepted HEAD maps through its recorded integrated commit to the exact deployed release. A lane that is deployed but lacks a retirement disposition or precise blocker fails the post-deploy gate.

## Retire App-managed and permanent worktrees

- `retirementPolicy` records what the coordinator must attempt at the applicable checkpoint; it is not an App trigger. Task completion, review merge, or deployment does not itself archive a task.
- Archive an App task only under recorded `archiveTasks` authority, passing its exact `threadId` and `hostId` when the current operation supports them. Never omit `threadId` when the intent is to archive another task. Verify the background archive through the current archived-task listing or equivalent App task state before calling it complete.
- When policy requires archive and authority is available, call the archive operation once and read back current archived-task state. Classify an accepted request that is not yet visible as `app-cleanup-pending`; do not blindly repeat it. When authority is pending or denied, keep the task and record the exact authorization blocker rather than implying that policy performed the action.
- Current Codex behavior may automatically remove an archived Codex-managed worktree after saving a restorable snapshot. Do not assume deletion is immediate, but do not treat an expected, verified App removal as a ledger mismatch.
- Permanent worktrees are not ordinary disposable lane worktrees. Archiving a chat does not authorize deletion of a permanent worktree.
- Never manually remove an App-managed or permanent worktree. Leave physical lifecycle to the App and report pending or retained state.
- Handoff moves task and Git state between environments; it is not archive or cleanup. Use a separate, explicitly authorized migration workflow when handoff is requested.

## Retire coordinator-manual worktrees

Remove a manual worktree only when all of the following hold:

- `removeManualWorktrees` is authorized;
- the review is merged, or abandonment is explicit and the lane HEAD is preserved on a recoverable remote ref;
- for a merge or fast-forward integration, the intended target contains the delivered HEAD or recorded merge commit;
- for a squash or rebase integration that does not contain the source HEAD, authoritative review state identifies the resulting commit, that commit is contained in the intended target, and the source HEAD remains on a recoverable ref;
- no task or workflow owns the lane;
- `git worktree list --porcelain` maps the exact absolute path to the expected branch and HEAD;
- `git -C <absolute-path> status --porcelain` is empty.

Use `git worktree remove <absolute-path>` followed by `git worktree prune`. Never use a glob, unresolved variable, broad parent directory, `rm -rf`, or force removal as the default path.

Delete a local branch only under `deleteBranches` authority and after merged or preserved state is proven. Delete a remote branch only when explicit authorization or repository policy clearly permits it. Retire an integration branch only after the umbrella review is merged and no open child review targets it.

When any condition fails, retain the lane, set `retained-blocked` with a precise `retirement.blockerReason`, and report the safest next action.
