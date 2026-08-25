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
