# Delivery Ledger

Use one ledger for one repository and delivery graph. Its purpose is to make authority, ownership, task provisioning, Git state, review state, and retirement state resumable without treating transient task titles as durable identity.

## Choose a location

Record `ledgerLocation` before dispatch:

- `coordinator-thread`: default; publish a complete checkpoint in the coordinator task whenever authority or lane state changes.
- an explicit repository or external path: use only when the user authorized writing that artifact.

Do not silently add a coordination file to the business repository. If the ledger is thread-scoped, include the full current ledger in handoff and recovery checkpoints rather than only a delta.

## Minimum schema

```yaml
delivery:
  id: null
  repository: null
  mode: plan-only
  ledgerLocation: coordinator-thread
  coordinator:
    title: null
    threadId: null
    hostId: null
    projectId: null
    handoffs: []
  modelRouting:
    mode: adaptive-profile
    profile: sol-first-adaptive
    source: skill-default
    accountContext: null
  authority:
    createTasks: {state: pending, source: null}
    createListener: {state: pending, source: null}
    pushBranches: {state: pending, source: null}
    openReviews: {state: pending, source: null}
    merge: {state: pending, source: null}
    deploy: {state: pending, source: null}
    syncBaseCheckout: {state: pending, source: null}
    archiveTasks: {state: pending, source: null}
    deleteBranches: {state: pending, source: null}
    removeManualWorktrees: {state: pending, source: null}
  base:
    remote: null
    finalBranch: null
    resolutionSource: null
    checkout: null
    syncOwner: null
    fixedSha: null
    syncStatus: null
  integration:
    branch: null
    reviewUrl: null
    status: planned
  release:
    activeBatchId: null
    batches:
      - id: null
        target: null
        plannedRelease: null
        deployedTarget: null
        deployedRelease: null
        deploymentVerified: null
        status: planning
        preDeployGate: {state: not-run, evidence: []}
        postDeployGate: {state: not-run, evidence: []}
  observer:
    lifecycle: absent
    clientThreadId: null
    threadId: null
    hostId: null
    projectId: null
    projectKind: null
    isGitRepository: null
    projectPath: null
    model: {value: null, source: configured-default}
    reasoning: {value: null, source: configured-default}
    selectionReason: null
    plannedLaneIds: []
    activeLaneIds: []
    overflowLaneIds: []

lanes:
  - id: null
    scope: null
    excludedScope: []
    dependencies: []
    executionSurface: codex-app-worktree
    routingRisk: null
    difficultySource: null
    model: {value: null, source: skill-default-adaptive-profile}
    reasoning: {value: null, source: skill-default-adaptive-profile}
    selectionReason: null
    task:
      lifecycle: planned
      clientThreadId: null
      threadId: null
      hostId: null
      projectId: null
      archiveState: not-requested
    placement:
      owner: codex-app
      worktreeKind: codex-managed
      path: null
      pathState: unknown
      retirementPolicy: report-only
    git:
      baseBranch: null
      baseSha: null
      branch: null
      head: null
      reviewTarget: null
      reviewUrl: null
    verification:
      commands: []
      result: not-run
      baselineFailures: []
    acceptance:
      state: not-reviewed
      acceptedHead: null
      evidence: []
    notification:
      owner: target-self
      coordinatorThreadId: null
      coordinatorHostId: null
      cursor: null
      activeCycle:
        id: null
        startCursor: null
        reason: initial
        handoffId: null
      eventReceipts: []
    observer:
      registered: false
      cycleId: null
      cursor: null
      rearmState: not-requested
      noticeReceipts: []
    releases:
      - batchId: null
        releaseDisposition: null
        dispositionReason: null
        acceptedHead: null
        integratedCommit: null
        integrationEvidence: []
        deployedTarget: null
        deployedRelease: null
        deploymentVerified: null
        deploymentEvidence: []
    status: planned
    retirement:
      disposition: null
      blockerReason: null
      recoveryRef: null
      snapshotState: unknown
```

Use explicit empty values when a field is not applicable. Do not fabricate a `threadId`, worktree path, review URL, test result, or delivery disposition.

## State vocabularies

### Action authority

- Each authority state is `pending`, `authorized`, or `denied`, with the exact user instruction or applicable policy recorded in `source`.
- An authorization applies only to its named action. In particular, `pushBranches` does not grant `openReviews`, and `merge` does not grant `syncBaseCheckout`, archive, or retirement actions.
- Delivery mode is `plan-only`, `local-delivery`, `branch-delivery`, or `review-delivery`; it summarizes the intended terminal artifact but never overrides an individual authority field.

### Model routing

- `delivery.modelRouting.mode` is `adaptive-profile` by default. Use `explicit-pins` for exact user-selected task settings and `configured-default` only when the user explicitly requests no task-level overrides. A higher-priority applicable instruction may replace any mode.
- The default profile is `sol-first-adaptive`. `accountContext` is user-reported context such as `Pro 20x`, not a claim that the coordinator verified account entitlements and not a reason to switch profiles.
- Model and reasoning sources are `inherited`, `configured-default`, `explicit-user-choice`, `skill-default-adaptive-profile`, or `higher-priority-policy`. Every adaptive selection records `routingRisk` (`routine`, `elevated`, or `critical`), `difficultySource` (`throughput`, `execution`, or `judgment`), and a concise `selectionReason`.
- Adaptive implementation lanes use Sol by default. Classify risk from error consequences, authority boundaries, persistent state, rollback quality, unresolved ambiguity, and verification difficulty; task size alone is not a risk class. Routine work uses medium, elevated risk sets high as the minimum effort, and critical risk sets xhigh as the minimum. Never automatically select max or ultra.
- Terra or Luna requires an exact user selection, a higher-priority policy, or an explicit user request prioritizing economy or high throughput. Without an exact model pin, Terra is limited to bounded implementation with reliable verification and Luna to repetitive, mechanical, high-volume work with deterministic checks; preserve the task's reasoning-effort floor.
- Do not reuse the model or reasoning strength of the last manually created task as a routing source. On resume or coordinator handoff, preserve the recorded profile and per-lane selections, but reassess settings for newly scoped lanes and review-fix cycles.
- A coordinator recommendation is not a self-applied setting change. The user changes the coordinator task's own model or reasoning strength; the coordinator applies the default adaptive profile only to new implementation App tasks and supported follow-up overrides.

### Task lifecycle

- `planned`: not created.
- `setup-pending`: creation returned only a provisioning handle such as `clientThreadId`.
- `ready`: real `threadId` and `hostId` resolved.
- `active`: implementation or review-fix work is running.
- `needs-attention`: the owning task requires a user or coordinator decision.
- `terminal`: the current task turn ended; the lane may still need review or retirement.
- `archived`: App archive state has been verified.
- `creation-failed`: no usable task was created.

Never use a provisioning handle where a real `threadId` is required.

### Lane status

- `planned`, `active`, `local-complete`, `review`, `merge-ready`, `merged`, `abandoned`, `retirement-pending`, `retired`, `retained-blocked`, or `retained-permanent`.
- When `retained-blocked`, set `retirement.blockerReason`, such as `unmerged`, `unpushed`, `dirty`, `active-owner`, `ledger-mismatch`, `unknown-path`, or `unrecoverable-head`.

### Integration status

- `planned`: no integration branch is active yet.
- `local-only`: local integration exists and remote review delivery was not requested.
- `remote-branch-only`: an authorized remote branch exists, but review creation was explicitly declined.
- `remote-review-pending`: remote review is intended and local work is ready, but `pushBranches`, `openReviews`, or both are not authorized.
- `draft`, `review`, `merge-ready`, `merged`, or `abandoned`: use only when supported by current branch and review evidence.

### Acceptance

- `acceptance.state` is `not-reviewed`, `accepted`, `rejected`, or `blocked`. Worker completion and passing tests do not imply coordinator acceptance.
- Set `acceptance.acceptedHead` only when state is `accepted`, using the exact reviewed source HEAD and current evidence. Every `include` or `defer` release record must repeat that same HEAD; a mismatch means the lane changed after acceptance and must be reviewed again.

### Release batches

- A release batch is the durable reconciliation boundary for one intended deployment. Give it a stable `id`, explicit target, planned or immutable deployed release identifier, and status `planning`, `pre-deploy-ready`, `deploying`, `deployed`, `post-deploy-verified`, or `blocked`.
- Keep prior batches and lane release records after a new batch starts. Set `delivery.release.activeBatchId` to the batch currently being reconciled; never overwrite an earlier batch to make a later gate pass.
- For every completed lane not already settled by a verified prior `include` or a reasoned `not-applicable` record, add exactly one record for the active batch. `releaseDisposition` is `include`, `defer`, `blocked`, or `not-applicable`. A deferred or blocked lane remains visible to later batches.
- `acceptedHead` is the exact source HEAD independently accepted by the coordinator. It must still match the lane's current source HEAD and have acceptance evidence. `integratedCommit` is the exact commit contained in the release target after merge, squash, rebase, or fast-forward integration; record current containment proof in `integrationEvidence`. Do not treat a lane's self-report, MR state, or moving branch name as either value.
- `include` requires `acceptedHead`, `integratedCommit`, and integration evidence before deployment. `defer` requires `acceptedHead`. `blocked` may leave acceptance or integration empty only when `dispositionReason` names that missing gate. Every `defer`, `blocked`, and `not-applicable` record requires a reason.
- After deployment, every included record repeats the exact `deployedTarget` and immutable `deployedRelease`, sets `deploymentVerified` only from current evidence, and records that evidence. The batch may become `post-deploy-verified` only when every included lane is verified and retirement-reconciled.
- `preDeployGate` and `postDeployGate` are `not-run`, `passed`, or `failed`. Record the validator command, result, batch ID, and evidence. A passing script result does not authorize deployment and cannot replace live release verification.

### Notification and observation

- `notification.owner` remains `target-self`.
- Delivery disposition is `not-attempted`, `delivered`, `retried-delivered`, or `undelivered`.
- Before the initial task turn, every review-fix turn, and every coordinator-routing handoff, the coordinator assigns a new stable `notification.activeCycle.id` and includes it as `notificationCycleId` in the target brief or routing update. Never reuse a cycle ID. Set `reason` to `initial`, `review-fix`, or `coordinator-handoff`; set `handoffId` only for a handoff cycle. Set `startCursor` to the reliable cursor immediately before that cycle, or leave it empty when none exists.
- Keep `notification.eventReceipts` until lane retirement. Each logical event receipt has this shape:

```yaml
receiptId: null
cycleId: null
status: null
cursorAliases: []
noticeIdAliases: []
deliveries: []
verification: {state: observed, evidence: []}
effects: []
```

- `receiptId` is coordinator-generated and stable. `cursorAliases` and `noticeIdAliases` correlate direct waits, target self-notifications, and observer notices to the same receipt. A delivery entry records source (`wait`, `target-self`, or `observer`), disposition, and evidence. Verification state is `observed`, `verified`, `rejected`, or `ambiguous`.
- Correlate an input only when its exact task handle and cycle ID match and a cursor alias, notice ID alias, or current task-state check supports the mapping. A terminal status is unique only inside a proven cycle. Multiple `needs_attention` events in one cycle require distinct cursors or notice IDs that are unique within that cycle and reused only for transport retry. An uncorrelated or stale-cycle input is a wakeup or delivery record only and cannot trigger effects; only a `verified` receipt may create effect entries.
- Before acceptance, user reporting, merge, or another effect, append an effect entry with a deterministic idempotency key and state `pending`. After success, set it to `complete` with evidence. On resume, reconcile a `pending` effect against current destination state; mark it `complete` if already applied, retry only when current authorization and an idempotent or preconditioned operation make that safe, otherwise set `reconcile-required`. Never infer success or blindly replay it.
- When a later duplicate supplies a missing cursor or delivery result, add that alias or evidence to the existing receipt without replaying completed effects. Preserve completed-cycle receipts; starting a new cycle changes `activeCycle` but never clears prior receipts.
- An optional listener is recorded as an observer only. Its lifecycle values (`absent`, `setup-pending`, `ready`, `unsupported`, `inactive`, `archived`, `creation-failed`) are protocol states, not Codex product states.
- Store listener provisioning and identity once in `delivery.observer`; never copy `clientThreadId` into `threadId`. `plannedLaneIds`, `activeLaneIds`, and `overflowLaneIds` reference lane records containing the exact target handles. Lane observer fields record target registration, observer cursor, and per-event notice receipts without duplicating listener identity.
- `observer.rearmState` is `not-requested`, `ready`, or `blocked-no-terminal-cursor`. Store observer delivery attempts per event in `observer.noticeReceipts`; do not carry one cycle's delivery disposition into another. If the previous terminal cursor is unavailable, a new target-self cycle may proceed with a new cycle ID, but observer registration and cursor-based direct waiting remain blocked until a reliable boundary cursor is recovered.

### Base and retirement

- Base status is `base-sync-current`, `base-sync-pending`, or `base-sync-blocked`.
- Retirement dispositions are defined in [the base synchronization and retirement protocol](base-sync-and-retirement.md). Do not invent a success classification when evidence is incomplete.
- Map `manual-retired` and `app-auto-cleaned-restorable` to lane status `retired`; map `cleanup-ready` and `app-cleanup-pending` to `retirement-pending`; map dirty, active, or blocked retention to `retained-blocked`; map `permanent-retained` to `retained-permanent` without inventing a blocker.
- `task.archiveState` is `not-requested`, `requested`, `archived`, or `verification-failed`. `placement.pathState` is `unknown`, `current`, or `historical`. `retirement.snapshotState` is `unknown`, `not-applicable`, `preserved`, or `missing`.

### Coordinator handoff

- Append one `coordinator.handoffs` record whenever coordination moves to a different task. Record a stable handoff ID; exact source and destination thread and host IDs; `sourceLaneIds`; `inheritedLaneIds`; per-lane routing updates; terminal-lane reconciliations; state `reconciling`, `complete`, or `blocked`; and evidence.

```yaml
id: null
from: {threadId: null, hostId: null}
to: {threadId: null, hostId: null}
sourceLaneIds: []
nonterminalLaneIds: []
terminalLaneIds: []
inheritedLaneIds: []
routingUpdates: []
terminalReconciliations: []
state: reconciling
evidence: []
```

- `sourceLaneIds` contains every lane not already retired at the source checkpoint. The destination imports all of them, including deferred, blocked, completed, and retirement-pending lanes; it does not select only active or recently notified tasks.
- For each nonterminal target, preserve prior receipts, assign a new `notificationCycleId` for the handoff route, update the exact coordinator address, and record delivery or an honest blocker. For each terminal target, preserve the old receipt and immediately record acceptance, release-disposition, and retirement reconciliation instead of starting an empty follow-up turn.
- Mark the handoff complete only when `sourceLaneIds` and `inheritedLaneIds` match, every nonterminal route points to the new coordinator or has a blocker, and every terminal lane has a recorded reconciliation result.

## Checkpoint invariants

At every dispatch, review handback, merge, release, base sync, and retirement checkpoint, verify:

1. One implementation owner per mutable scope.
2. One coordinator and one base synchronization owner per delivery graph.
3. Each external action is `authorized`, `denied`, or `pending`; every non-pending state has a recorded source.
4. Every ready App task has a real `threadId` and `hostId`; setup-pending tasks do not.
5. Branch, base SHA, review target, current HEAD, and tests reflect current evidence.
6. `target-self` remains the notification owner; a listener, if explicitly requested, is only an observer.
7. Every observed completion or attention event has a durable receipt. Each effect has its own idempotency key, state, and evidence; duplicates never directly trigger effects, and interrupted `pending` effects are reconciled before any retry.
8. Every `retained-blocked` lane has a specific blocker and recoverable next action. Every `retained-permanent` lane has an explicit permanent owner and retirement policy.
9. Every uncovered completed lane has exactly one disposition in the active release batch; included and deferred lanes have acceptance evidence, and included lanes have integration evidence.
10. Before deployment, the active batch passed the pre-deploy gate. Before the final report, every included lane has verified deployment evidence plus a retirement disposition or precise blocker, and the post-deploy gate passed.
