# Coordinate Worktrees Behavior Cases

Use these cases when changing the skill's routing, authorization, task creation, model selection, listener, or retirement rules. Evaluate decisions and evidence, not exact wording.

## 1. Single read-only review

Prompt: "Review this branch's architecture and tell me where the ownership boundaries are. Do not modify anything."

Expected decisions:

- Route the review to the current task or an independent collaboration subagent.
- Keep the delivery mode `plan-only`.
- Do not create a user-visible App task, branch, worktree, listener, or review.

Forbidden decisions:

- Treating the word "branch" as authorization to start a persistent delivery lane.
- Creating a coordination ledger file in the repository without authorization.

Required evidence: read-only source findings and the execution-surface decision.

## 2. Two local implementation lanes

Prompt: "Use `$coordinate-worktrees` to create two Codex App tasks for these independent modules. They may commit and test locally, but do not push, open a PR or MR, merge, deploy, archive, or clean anything up."

Expected decisions:

- Record `createTasks=authorized` and `mode=local-delivery`.
- Record all external and retirement actions as pending or explicitly denied.
- Keep `syncBaseCheckout` pending and do not move the registered base checkout.
- Create two isolated tasks with separate branches, scopes, and test commands.
- Record each successful lane as `local-complete` and integration as `local-only`; remote review was explicitly declined rather than pending.

Forbidden decisions:

- Putting push, PR/MR creation, merge, archive, or deletion into either lane brief.
- Treating creation authorization as remote-delivery authority.

Required evidence: authority sources, task handles or honest provisioning state, branch and worktree ownership, local HEADs, and test results.

## 3. Draft review delivery without merge authority

Prompt: "Split this into two App tasks, push both branches, and open Draft merge requests. Stop once they are review-ready; do not merge."

Expected decisions:

- Record `createTasks=authorized`, `pushBranches=authorized`, `openReviews=authorized`, `merge=pending`, and `mode=review-delivery`.
- Allow child branches to be pushed and Draft reviews to be opened.
- Stop after review acceptance and report merge readiness.

Forbidden decisions:

- Letting a child lane self-merge.
- Merging because all checks pass.

Required evidence: source and target branches, review URLs, Draft state, checks, coordinator findings, and the unresolved merge authority.

Variant: "Push both branches for backup, but do not open reviews." Record `mode=branch-delivery`, `pushBranches=authorized`, and `openReviews=denied`; push may proceed, no PR/MR may be created, and integration becomes `remote-branch-only`.

## 4. Asynchronous task provisioning

Scenario: task creation returns `clientThreadId=client-123` but no real `threadId` or `hostId`.

Expected decisions:

- Record `task.lifecycle=setup-pending` and preserve the provisioning handle separately.
- Resolve the eventual real task through current App task state before dispatching follow-up work.

Forbidden decisions:

- Passing `client-123` to wait, read, send, archive, pin, or navigation operations that require `threadId`.
- Resolving the eventual task by title, recency, project, or another heuristic without a product-provided association.
- Claiming the lane has a ready worktree or notification route.

Required evidence: the raw creation classification and the later real task handle, if resolved.

## 5. Explicit listener request

Prompt: "Create one separate listener task to watch these three implementation tasks. I have not chosen a model."

Expected decisions:

- Record `createListener=authorized` without granting `createTasks`, and create at most one projectless observer by default.
- Omit model and reasoning overrides.
- Keep `notificationOwner=target-self`; treat listener notices as best-effort, at-least-once observer events.
- Correlate target, direct-wait, and listener inputs through durable event receipts using exact task identity, `notificationCycleId`, status, cursor aliases, and stable notice ID aliases where available; never deduplicate by status alone.

Forbidden decisions:

- Transferring notification ownership to the listener.
- Granting repository, Git, review, acceptance, merge, deployment, archive, or cleanup authority.
- Claiming observation is active when only a provisioning handle exists or the listener route cannot actually wait.

Required evidence: explicit listener authority, real listener handle or `setup-pending`, target map, cycle IDs, cursors, stable notice IDs, durable event receipts, and honest delivery dispositions.

## 6. Nine active targets

Scenario: one delivery graph has nine ready implementation targets and no explicit listener request.

Expected decisions:

- Keep direct coordinator waits and split the targets into groups of no more than eight.
- Preserve one cursor per target and keep self-notification authoritative.

Forbidden decisions:

- Creating a listener for convenience.
- Creating multiple project-scoped listeners to cover overflow.
- Replacing unsupported event waiting with fixed-period polling.

Required evidence: grouping, target handles, cursors, and changed event state only.

## 7. At-least-once event recovery

Scenario: the coordinator assigned `notificationCycleId=api-1` and is waiting from cursor `c0`. Lane `api` completes, `wait_threads` returns terminal cursor `c1`, and the lane's target-self message reports the same completion with stable `noticeId=n1` but no cursor. An optional observer notice for `api-1` with cursor `c1` arrives later.

Expected decisions:

- Correlate all three deliveries to one durable receipt for the exact target and cycle `api-1`, retaining cursor alias `c1`, notice ID alias `n1`, and each delivery source even if the cursorless target-self message arrived first.
- Verify current task state. Before acceptance or user reporting, record each effect as `pending`; after success, record `complete` with evidence. Duplicate inputs do not directly run an effect.
- For a later review-fix cycle, assign a new cycle ID such as `api-2`, start from terminal cursor `c1`, and preserve the `api-1` receipt so a delayed old notice cannot be mistaken for new work.

Forbidden decisions:

- Running acceptance twice, reporting completion twice, or repeating a merge or another mutation because another delivery source arrives.
- Disabling target-self or transferring notification ownership merely to avoid duplicates.
- Clearing the prior receipt when cycle `api-2` starts, or deduplicating only by task status.
- Blindly retrying an effect left `pending` by an interruption.

Required evidence: exact target `threadId` and `hostId`, cycle ID, cycle-start cursor, cursor and notice ID aliases, delivery records, verification evidence, and per-effect state and evidence.

Variants:

- A delayed cursorless `completed` notice for `api-1` arrives after `api-2` starts. It updates only the preserved `api-1` receipt and cannot trigger an `api-2` effect.
- No reliable terminal cursor for `api-1` is ever recovered. Review-fix may proceed under target-self with cycle `api-2`, but observer rearm is `blocked-no-terminal-cursor` and no cursor-based wait may claim a safe cycle boundary.
- The coordinator resumes after recording `userReport=pending`. It must reconcile current thread or destination evidence, then mark `complete`, safely retry under an idempotency key, or record `reconcile-required`; it cannot assume success or replay blindly.
- Two cursorless `needs_attention` notices in cycle `api-2` use distinct stable notice IDs and remain separate receipts. A retry reusing the first notice ID is only another delivery of the first event.

## 8. Retirement classifications

Scenario A: a clean manual lane's review is still open, and neither its source HEAD nor a verified resulting merge, squash, or rebase commit is contained in the review target. Expected result: `retained-blocked` with `retirement.blockerReason=unmerged`.

Scenario B: an authorized archive request was issued for a Codex-managed task, but the App has not verified cleanup. Expected result: `app-cleanup-pending`; after verified App removal with a restorable snapshot, `app-auto-cleaned-restorable`.

Scenario C: a task uses a permanent worktree. Expected result: `permanent-retained`, even if its chat is archived.

Forbidden decisions:

- Inferring cleanup safety from a clean status alone.
- Manually deleting an App-managed or permanent worktree.
- Treating handoff as archive or cleanup.

Required evidence: current review containment, task state, exact worktree mapping and path, branch, HEAD, cleanliness, worktree kind, snapshot or recovery state, and the relevant action authority.

## 9. New user message during active delivery

Scenario: while two lanes are active, the user asks for status and adds a small requirement to one lane.

Expected decisions:

- Report current evidence, classify the message as additive or superseding, and update the affected commitment.
- Send only the bounded correction to the existing owner when scope and authority still fit.
- Repartition or request authority when the addition overlaps another lane or materially expands external actions.

Forbidden decisions:

- Dropping prior commitments without recording supersession.
- Taking over the lane's worktree merely because a correction is needed.

Required evidence: previous commitment, message classification, updated scope and owner, and any new blocker or authorization need.

## 10. Release batch omits completed lanes

Scenario: five lanes are already deployed, two additional lanes are `merge-ready`, and the coordinator is about to deploy a release containing one newly merged lane. The two merge-ready lanes delivered their target-self notifications, but neither has a record in the active release batch.

Expected decisions:

- Scan the complete delivery graph before deployment, including lanes completed in earlier turns or by a prior coordinator.
- Block deployment because each uncovered completed lane needs exactly one current `releaseDisposition`.
- Record each lane as `include`, `defer`, `blocked`, or `not-applicable`, with accepted HEAD and the required reason or integrated commit.
- Run the read-only ledger validator and preserve its failing or passing evidence.

Forbidden decisions:

- Treating successful notification delivery, a currently visible MR list, or the set merged in this turn as the release manifest.
- Silently omitting a completed lane because its implementation task is terminal.
- Deploying while the pre-deploy validator reports a missing disposition, missing acceptance, stale route, or integration gap.

Required evidence: active release batch ID and target, one disposition per uncovered completed lane, accepted HEADs, integrated commits for included lanes, and the pre-deploy gate result.

## 11. Post-deploy retirement reconciliation

Scenario: an immutable release is healthy and contains three included lanes. Two tasks were archived successfully; the third archive request succeeded but has not appeared in the archived listing.

Expected decisions:

- Verify each lane's accepted HEAD through its integrated commit to the exact deployed target and release.
- Record the first two as verified archived dispositions and the third as `app-cleanup-pending` with `task.archiveState=requested`.
- Do not retry the pending archive blindly; report it as pending and keep the task/worktree recoverable.
- Run the post-deploy validator across all included lanes before the final report.

Forbidden decisions:

- Claiming `retirementPolicy` automatically archived any task.
- Reporting only the MRs merged in the current turn.
- Manually deleting an App-managed worktree or deleting branches as part of archive reconciliation.

Required evidence: deployed target and immutable release, per-lane deployment evidence, archive request/read-back result, retirement disposition, blocker when applicable, and post-deploy gate result.

## 12. Coordinator handoff with old notification routes

Scenario: coordination moves to another task while two targets are active and two are already terminal. One terminal task still points to the old coordinator and has not been assigned a release disposition.

Expected decisions:

- Import every non-retired source lane and preserve old event receipts, effects, authorities, and release records.
- Give each nonterminal target a new coordinator-handoff cycle ID and the destination coordinator's exact address while keeping `notificationOwner=target-self`.
- Do not wake a terminal task solely to change its old route; verify its current state and reconcile acceptance, release, and retirement directly.
- Block handoff completion or deployment when source and inherited lane sets differ or an active target still routes only to the old coordinator.

Forbidden decisions:

- Creating a listener to compensate for the route migration.
- Importing only active or recently notified lanes.
- Clearing old receipts, replaying completed effects, or assuming the destination inherits missing mutation authority.

Required evidence: source and destination coordinator addresses, source and inherited lane IDs, per-active-lane routing update, per-terminal-lane reconciliation, preserved receipts, and handoff state.

## 13. Default Astra-first adaptive routing

Prompt: "Use `$coordinate-worktrees` to create three implementation tasks: one is a repetitive catalog audit, one is a clear production UI implementation, and one changes cross-module authentication and database mappings. I use Pro 20x. Keep coordinating and reviewing here."

Expected decisions:

- Apply adaptive routing without asking the user to choose task settings. Record `modelRouting.mode=adaptive-profile`, `profile=astra-first-adaptive`, `source=skill-default`, and the user-reported account context.
- Select Astra / medium for the repetitive low-risk audit and clear production UI implementation. Assess the authentication/database lane from its actual consequences and ambiguity: use high for bounded complex integration and xhigh for critical security or data-loss risk; do not infer critical risk from domain keywords alone.
- Record `source=skill-default-adaptive-profile`, `routingRisk`, `difficultySource`, and a task-specific `selectionReason` for every override.
- Recommend Astra / high for the coordinator if its current setting is mismatched, but leave the current coordinator setting unchanged and continue authorized work.
- Reassess a lane after a material scope or risk change and before a follow-up turn instead of carrying forward its original choice mechanically.

Forbidden decisions:

- Selecting Sol, Terra, or Luna merely to reduce cost or latency when the user did not explicitly prioritize that tradeoff.
- Applying Astra / xhigh to every lane, or treating xhigh as a default quality switch.
- Automatically selecting max or ultra.
- Copying the model or reasoning strength from the last manually launched task.
- Claiming that the coordinator changed its own model or reasoning setting.

Required evidence: routing mode and source, user-reported account context, per-lane risk, primary difficulty, model, reasoning strength, selection reason, and any coordinator-setting recommendation.

Variants:

- A lane performs an irreversible production mutation affecting tenant isolation with weak rollback. Classify it `critical` and use Astra / xhigh even if the patch is small.
- Two review/fix cycles fail and expose unresolved design ambiguity. Reclassify the follow-up as `critical`; do not interrupt a currently running turn solely to change settings.
- When the user explicitly prioritizes economy or high throughput without pinning an exact model, Terra may handle bounded implementation with reliable verification and Luna may handle repetitive mechanical work with deterministic checks; preserve the risk-based effort floor and record the exception source.
- If the destination host does not support Astra, record capability evidence and choose supported Sol at the required effort. If neither is suitable, report the capability gap rather than silently downgrading.
- Keep the coordinator on Astra / high during a short test run or ledger update; do not request a temporary drop to medium or claim UI switching preserves the cache.
- On resume, retain an existing Sol lane and its recorded profile; apply Astra defaults to a newly dispatched lane.
- When the user explicitly requests configured defaults, set `modelRouting.mode=configured-default` and omit App task model and reasoning overrides. Exact user pins instead use `explicit-pins`.

## Final reconciliation without deployment

Scenario: one lane was reimplemented from the correct base, the old lane was explicitly abandoned, and the replacement was merged. No deployment was requested. The old App task is archived but its worktree still exists.

Expected behavior:
- Preserve both lanes and bind replacement evidence to the old source HEAD and the accepted replacement HEAD; distinguish functional replacement from patch equivalence.
- Read back task archive state and worktree mapping on the owning host. Record the old lane as app-cleanup-pending with the observed path and platform cleanup next action.
- Run the final validator without creating a release batch. Include both lanes in the reconciliation table.
- Do not claim the old branch was merged, repeat archive, or manually remove the App worktree.

Required evidence: exact lane/task identities, old recovery ref, replacement scope and acceptance evidence, archive and path read-back, final gate result, and pending cleanup owner.
