# Coordinator Message and Commitment Protocol

Use this protocol when the registered coordinator receives another user message while lanes, listener targets, or delivery commitments remain active.

## Classify the message before acting

| Class | Signal | Coordinator action |
| --- | --- | --- |
| Additive | Follow-up request, status question, investigation, or new priority | Answer or append work while preserving active task and commitment lifecycle; a priority may reorder the coordinator queue but does not silently redirect a lane |
| Lifecycle change | The user explicitly says cancel, stop, replace, pause, or equivalent and identifies the exact target | Change only that target's lifecycle and record the decision |
| Ambiguous | The message could affect existing work but names no exact target or lifecycle intent | Treat it as additive, keep work running, and ask for precision only when needed |

- Never cancel, pause, interrupt, redirect, archive, or discard an implementation task, listener target, or unfinished coordination commitment merely because a new message arrived.
- Do not send an interrupt to a child task unless the user explicitly requests stopping that exact task.
- If the new request is independent, create a new authorized lane or place it in the coordinator queue. If it touches the same files or mutable state as an existing lane, keep one owner and append the work sequentially.
- When the user says not to interrupt tasks, answer or investigate the current question without changing active task lifecycle, then resume the existing coordination work.

## Recover after a product steer

New user input can end an active `wait_threads` call or the coordinator's current turn early. Do not claim that the platform will never interrupt a wait. After handling the message:

1. Reload the registered coordinator identity and rebuild the active lane and commitment ledger from current task state.
2. Restore every active lane's owner, exact task handle, scope, branch or worktree, status, and pending checkpoint. Restore listener targets and their latest cursors without dropping them.
3. Reconcile the coordinator queue using the additive and file-ownership rules above; do not infer cancellation from absence or ambiguity.
4. Resume unfinished independent acceptance, merge or authorization decisions, deployment, base synchronization, and worktree retirement checkpoints.
5. Re-enter event-driven waits with current cursors when waiting is still the next action.

Completion criterion: responding to a later message changes only explicitly targeted lifecycle state, while every other lane, listener target, and recorded delivery commitment remains owned and resumable.

## Transfer coordinator ownership

Use a ledger handoff when a different task becomes the coordinator. A task handoff or a copied summary does not by itself transfer notification routing, release ownership, or retirement commitments.

1. The source checkpoint records the old coordinator's exact address, every non-retired lane, current task and Git state, all event receipts and pending effects, every release batch and disposition, authorities, and pending acceptance, deployment, base-sync, archive, and retirement actions.
2. The destination records its exact coordinator address and imports the complete source lane set. Compare `sourceLaneIds` with `inheritedLaneIds`; a missing lane blocks completion even if that lane is terminal or was created before the current release.
3. For each nonterminal target, preserve old receipts, assign a new `notificationCycleId` marked as a coordinator-handoff cycle, and send a bounded routing update containing the new coordinator `threadId` and `hostId`. Record delivery or an honest blocker. Do not create a listener or change `notificationOwner=target-self` to compensate for stale routing.
4. For each terminal target, do not start a no-op follow-up merely to change its address. Import its terminal receipt, verify current task, Git, and review state, then immediately record acceptance, current release disposition, and retirement status.
5. Rebuild the active release batch across the complete inherited lane set. Completed lanes require `include`, `defer`, `blocked`, or `not-applicable` before any deployment; a lane is not exempt because its completion notice went to the old coordinator.
6. Mark the handoff complete only after all lanes are inherited, all nonterminal routes are updated or blocked explicitly, terminal lanes are reconciled, and unfinished effects remain resumable without replay.

The destination coordinator owns subsequent verification, but it does not inherit authority that the source never had. Preserve the recorded source for every action authority and request new authorization when the destination's intended action is outside it.
