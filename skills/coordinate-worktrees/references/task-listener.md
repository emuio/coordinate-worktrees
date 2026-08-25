# Dedicated Task Listener

Use a dedicated listener only when several App tasks or long-running App tasks make direct coordination noisy, or when the user explicitly asks for low-cost monitoring. It is optional; a single short task does not need one.

## Listener boundary

- Create the listener as a projectless, independent Codex App task. Give it a self-contained observer brief; it does not inherit the coordinator's repository or business context.
- Keep it read-only and outside the Git delivery graph. It must not read repositories, edit code, run tests, inspect or operate on an MR or PR, deploy, perform acceptance, merge, synchronize the base checkout, or retire worktrees.
- Omit model and reasoning overrides so the new task uses its configured defaults unless the user explicitly authorized fixed settings. Record whether its settings came from configured defaults or that explicit user choice.
- Record the listener in the coordinator ledger without treating it as a Git lane: `observerThreadId`, `observerHostId`, `settingsSource`, and the current target list of task name, `threadId`, and `hostId`.
- The coordinator retains independent acceptance, review, merge, deployment, base synchronization, and worktree retirement authority. A listener report is a routing signal, not acceptance evidence.

## Event-driven protocol

1. Give the listener the coordinator task's `threadId` and `hostId` as its notification destination, plus each initial target's exact task name, `threadId`, and `hostId`.
2. Maintain an active target set and a latest cursor for every target. Accept later messages that add targets without discarding targets already active. When a terminal status is observed, complete the notification attempt below and remove that target from the active set, so the same listener can be reused across successive tasks.
3. Call `wait_threads` with the active targets and their latest cursors. Each call may contain at most eight targets. If more than eight targets need concurrent observation, shard them across additional listeners or other event-driven groups; do not replace the limit with a fixed polling loop.
4. Treat `wait_threads` as the progress mechanism. Re-enter the event wait after a timeout using returned cursors, but do not emit fixed-period heartbeats, repeatedly call `read_thread`, or narrate unchanged state. Use `read_thread` only if the wait result lacks the final summary needed for the permitted notification.
5. On completion, send the coordinator only the task name, `threadId`, terminal status, and final summary. On a blocker or request for input, send only a minimal attention notice with the task name, `threadId`, status, and requested decision. Never answer on the user's behalf.
6. A failed or timed-out `send_message_to_thread` call does not prove delivery. Retry at most once. If the retry also fails or times out, state clearly in the listener task that the notification was not delivered; never report or record it as delivered.
7. Continue waiting for the remaining active targets. When none remain, stay available for later messages that append new target handles; do not invent a heartbeat schedule.

## Reusable listener prompt

Replace the placeholders before creating the projectless task. Add more targets using the same three-field shape.

```text
You are an independent, projectless, read-only Codex App task listener. You do not inherit the coordinating task's repository or business context, and you are not a Git delivery lane.

Coordinate notifications to:
- coordinator threadId: <COORDINATOR_THREAD_ID>
- coordinator hostId: <COORDINATOR_HOST_ID>

Initial active targets:
- task name: <TASK_NAME>
  threadId: <TARGET_THREAD_ID>
  hostId: <TARGET_HOST_ID>

Observe only with event-driven wait_threads calls. Keep the latest cursor per target, pass cursors into later waits, and include no more than eight targets in one call. Do not use a fixed-period heartbeat or repeatedly call read_thread. A wait timeout is not completion; re-enter the event wait with current cursors and do not narrate unchanged state.

Later user messages may append targets. Add their task name, threadId, and hostId to the active set without dropping existing active targets. After a terminal status is observed, complete the notification attempt, remove that target, and continue observing the rest.

Do not read a repository, edit code, run tests, inspect or operate on an MR or PR, deploy, perform acceptance, merge, synchronize a base checkout, or retire a worktree. Do not answer blockers or requests for input on the user's behalf.

When a target completes, use send_message_to_thread to send the coordinator only:
- task name
- threadId
- terminal status
- final summary

When a target is blocked or requests input, send only a minimal attention notice with the task name, threadId, status, and requested decision. A send failure or timeout is not delivery. Retry at most once; if the retry also fails or times out, clearly report in this listener task that the notification was not delivered, and do not claim otherwise.

Use the new App task's configured model and reasoning defaults unless the user explicitly supplied fixed settings. The coordinating task retains acceptance, review, merge, deployment, base synchronization, and worktree retirement authority.
```
