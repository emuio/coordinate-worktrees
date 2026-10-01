# Coordinator Message and Commitment Protocol

Use this protocol when the registered coordinator receives another user message while lanes, listener targets, or delivery commitments remain active.

## Execution surface selection

Apply this selection inside an already authorized coordination delivery; retain the skill's exclusion of standalone ordinary subagent work.

1. Reuse the existing owner and handle before selecting a new surface. Do not create a second owner for the same responsibility, move its worktree, or interrupt or migrate an active task just to change how it runs.
2. Decide whether the assignment ends with one bounded result or requires persistent independent ownership. A single group-message or evidence check fits a collaboration subagent; that does not require the entire integration spanning multiple days to remain a subagent. Bounded tests, documents, or edits can also use a scoped subagent when the coordinator has selected authorized paths and assigned exclusive files. A sustained delivery or full integration needing separate recovery and handoff fits an explicitly requested or already authorized App task.
3. Confirm owned files, absolute paths, mutable-state isolation, and action authority before dispatch. Code-changing persistent lanes use their independent worktrees; purely read-only persistent work may be projectless and reference existing read-only paths without a new branch or worktree. Read-only integration does not acquire a code-delivery lifecycle merely because its owner is persistent.
4. For explicitly requested long-term external-message reception (for example DWS), preprocessing, or cross-project routing, use a dedicated independent task with an existing or authorized event backend. Record explicit authority for that task, backend, and message routing in its brief; `createListener` authority for a child-task observer alone does not authorize external-message intake. Do not simulate persistence with a subagent that waits continuously. A bounded event lookup remains distinct from listener creation, and routing or preprocessing does not grant permission to send external replies or broaden the underlying integration scope. This external-message intake/routing role is distinct from the child-task status observer in `task-listener.md`; do not apply that observer protocol to DWS intake. Follow the relevant connector or plugin skill for message operations. This skill selects the execution surface, not a general DWS workflow.
5. Record a concise dispatch rationale in the coordinator brief or existing ledger: surface, selection reason, owner, absolute paths and owned files, completion condition or pending checkpoint, and scope/action authority. Distinguish a collaboration subagent from an App task in user-facing descriptions instead of calling both a “child window.” Select model and effort separately using the existing policy and exact user pins; elapsed time, model level, or file count alone must not drive a surface switch.

## Keep coordinator available

- Within existing action authority, prefer independent execution lanes for coding, lengthy builds or tests, and sustained integration work. Route external waiting through the owning lane or an existing event mechanism. Reuse the current owner and task handle; do not take over another lane's worktree or create an unnecessary parallel owner.
- Keep requirements, dispatch, interface decisions, evidence review, and acceptance in the coordinator. Necessary short verification and coordination actions that must be serialized may remain there; this is a routing preference, not a ban on direct checks.
- Preserve an owner, exact task or event handle, and pending checkpoint for every unfinished item. Request one correlated completion or `needs_attention` notification per cycle under the existing notification protocol, and process notices at meaningful checkpoints without duplicating its receipt or recovery rules.
- Use a bounded event-driven wait only when no other authorized work can advance and the next coordinator action depends on that event. Do not occupy the coordinator with continuous polling or repeated status reads; preserve the pending checkpoint when returning control.
- A separate execution lane keeps lengthy work out of the coordinator but does not guarantee immediate notification delivery while the coordinator is busy. Do not cancel the current turn or force an interrupt to accelerate delivery; handle available notices at safe checkpoints and continue the original objective unless the user explicitly changes it.
- This routing does not grant task or listener creation, remote writes, deployment, trust changes, or cleanup authority. Apply the recorded authority and the applicable project rules before taking any such action.

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
