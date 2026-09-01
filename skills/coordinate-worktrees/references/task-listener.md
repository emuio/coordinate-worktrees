# Optional Task Listener

Use this protocol only when the user explicitly requests a separate, user-visible listener task. Direct coordinator `wait_threads` and target self-notification are the ordinary path. Task count, task duration, coordinator convenience, or a desire to lower cost is not authorization to create another App task.

The listener is a best-effort observer. It never becomes the notification owner, implementation owner, acceptance authority, merge authority, deployment authority, base synchronization owner, or worktree retirement owner.

## Keep target-self authoritative

Every persistent implementation target keeps `notificationOwner=target-self` for every observation cycle:

```text
Notification routing:
- notificationOwner: target-self
- task name: <TASK_NAME>
- task threadId: <TARGET_THREAD_ID>
- task hostId: <TARGET_HOST_ID>
- notificationCycleId: <CYCLE_ID>
- coordinator title: <COORDINATOR_TITLE>
- coordinator threadId: <COORDINATOR_THREAD_ID>
- coordinator hostId: <COORDINATOR_HOST_ID>

On completion or needs_attention, send one concise notification to the exact coordinator threadId and hostId. Include notificationCycleId and a stable noticeId unique within that cycle and reused only if transport is retried; include a cursor only when actually available. A failed or timed-out send is not delivery; retry at most once, then record undelivered without claiming success. Do not send routine progress chatter.
```

A listener notice, a direct coordinator wait result, and a target self-notification can represent the same event. Treat all three as at-least-once inputs and correlate them to the coordinator's durable event receipt using the target `threadId`, `hostId`, `notificationCycleId`, status, event cursor, and stable `noticeId` where those fields exist. Later copies may add delivery evidence or a previously missing cursor but must not directly repeat effects. An input without a matching cycle ID, cursor, or other reliable correlation is only a wakeup until current task state resolves it. Do not attempt a non-atomic notification-owner transfer.

## Create only the explicitly requested listener

1. Confirm that the user explicitly asked for a separate listener task. Record the request as `createListener=authorized`; it does not grant `createTasks` for implementation lanes or authorize archiving, replacing, or migrating another task.
2. Resolve current thread capabilities by semantic operation rather than assuming a fixed tool namespace.
3. A listener needs no repository access. Use a projectless task unless the user explicitly requests association with a saved project. For an explicitly project-associated listener, call `list_projects`, record `projectKind`, `isGitRepository`, path and `hostId` when present, and follow the current `create_thread` environment contract. Do not hardcode `environment: local` for a Git project and do not route a ChatGPT project through the Codex worktree path.
4. Omit model and reasoning overrides unless the user explicitly chose them. If the user explicitly requests a low-cost profile, resolve a currently available compatible model and pass the requested settings; never turn one earlier choice into a permanent skill default.
5. Pass the complete observer brief as the initial creation prompt and set a searchable title when supported. Leave the listener unpinned unless the user requests pinning.
6. Classify listener creation as `ready` only when a real `threadId` and `hostId` are available. If creation returns only a `clientThreadId` or equivalent provisioning handle, record it in the listener checkpoint and set `listenerLifecycle=setup-pending`. Never use that handle as `threadId`, register targets through it, or claim observation is active. Resolve the real task only through a product-provided association in current App task state; never infer identity from title, recency, or project alone. If no reliable association is exposed, remain `setup-pending` and report the boundary. If creation returns no usable task or provisioning handle, record `listenerLifecycle=creation-failed`.

Create at most one listener for one delivery graph. While setup is pending, record the intended target set as `plannedLaneIds`; do not populate `activeLaneIds`. Keep at most eight active targets in the ready listener and put the rest in `overflowLaneIds` for coordinator-side grouped waits. Do not create a second listener without a new explicit user request.

The coordinator owns listener registration. When a terminal listener target frees capacity, the coordinator may promote one already authorized overflow lane by copying that lane's latest coordinator-side cursor, updating the planned, active, and overflow sets, and sending one bounded target-map update to the listener. The listener rebuilds the map after that message interrupts its wait and re-enters event waiting. Never transfer a stale cursor or promote a target outside the recorded delivery graph.

## Preserve the read-only boundary

The listener may only:

- call event-driven task wait or read operations;
- maintain target handles and cursors in its observer ledger;
- send concise observation notices to the exact coordinator address.

It must not read the repository, edit files, run tests, operate on Git or a PR or MR, message implementation tasks, answer requests for user input, accept work, merge, deploy, synchronize a base checkout, archive tasks, or retire worktrees.

## Follow the event-driven protocol

1. Register each target with task name, exact `threadId`, exact `hostId`, coordinator-assigned `notificationCycleId`, latest cursor when available, and `notificationOwner=target-self`.
2. Call `wait_threads` with one to eight active targets and their latest cursors. A timeout is not completion. New user input may end a wait; rebuild the target and cursor map, then re-enter the event wait.
3. Treat the listener's `ready`, `unsupported`, and `inactive` values as protocol ledger states, not Codex product task states. `ready` proves only that a real listener task and target map exist; it does not prove the listener is currently blocked in a wait. A returned listener event or timeout proves that a prior wait occurred, not that continuous future observation is active. Never report an `active-wait` or equivalent product state that the App does not expose.
4. If the actual listener route cannot wait on a target, record `listenerLifecycle=unsupported` with the semantic failure. Keep target-self routing, do not poll with repeated reads, do not recreate the listener, and do not claim active observation.
5. On a new completion or attention event, send the coordinator an observer notice containing task name, `threadId`, `hostId`, `notificationCycleId`, status, cursor when available, a stable `noticeId` unique within that cycle, and final summary or requested decision. Label it `observer-notice` so the coordinator can correlate it with direct waits and target self-notifications.
6. Retry a failed or timed-out notice at most once using the same `noticeId`. Record `delivered`, `retried-delivered`, or `undelivered` honestly.
7. After a terminal event, record its cursor outside the active set and remove the target. A `needs_attention` event is not automatically terminal: record its cursor, notify the coordinator, and keep the target registered unless current task state proves that observation cycle ended. Continue waiting from the latest cursor after the coordinator handles the decision.

Use `read_thread` only when a wait result lacks the minimal final summary needed for the permitted notice. Never replace unsupported event waiting with fixed-period polling.

## Observe a review follow-up

A terminal event closes one observation cycle. For a later review-fix cycle, the coordinator assigns a new `notificationCycleId` and explicitly re-registers the same target with that ID and its previous terminal cursor. The listener waits from that cursor and treats only later events as part of the new cycle.

Re-registration may occur before or after the coordinator sends the review-fix message because target-self remains authoritative throughout. Do not replay the prior terminal event, infer a new cycle from activity, or keep historical terminal targets permanently active.

If no reliable terminal cursor exists, record `blocked-no-terminal-cursor` and do not register that target with the listener for the new cycle. The coordinator may still send review-fix work with a new `notificationCycleId` and rely on target-self. Restore event-driven observation only after a reliable boundary cursor is recovered; never start an unbounded wait that could replay the old cycle.

## Do not migrate implicitly

An existing task's project association and host are not changed in place. Creating a replacement listener, moving it to another host, changing its environment, or archiving the old listener requires explicit user authorization for those actions. Do not treat a new App entry point or matching project name as migration authority.

## Reusable listener prompt

Replace placeholders before using this prompt:

```text
You are a strictly read-only Codex task observer. You were created because the user explicitly requested a separate listener task. You are not a Git delivery lane and do not inherit repository or business authority.

Notify only this coordinator:
- coordinator title: <COORDINATOR_TITLE>
- coordinator threadId: <COORDINATOR_THREAD_ID>
- coordinator hostId: <COORDINATOR_HOST_ID>

Observed targets:
- task name: <TASK_NAME>
  threadId: <TARGET_THREAD_ID>
  hostId: <TARGET_HOST_ID>
  notificationCycleId: <CYCLE_ID>
  cursor: <LATEST_CURSOR_OR_NONE>
  notificationOwner: target-self

Keep target-self as the authoritative notifier. Use event-driven wait_threads calls with the latest cursor for each target and at most eight active targets. A timeout is not completion. If a message interrupts a wait, rebuild the target map and wait again. Do not poll with repeated read_thread calls.

On a new terminal or needs_attention event, send the coordinator one observer-notice with task name, threadId, hostId, notificationCycleId, status, cursor when available, a stable noticeId unique within that cycle, and final summary or requested decision. Delivery is at-least-once; the coordinator correlates observer notices with direct waits and target self-notifications through its durable event receipt. Retry a failed send at most once with the same noticeId and never claim an unsuccessful delivery. For needs_attention, save the cursor and keep the target registered unless current task state proves that cycle ended; after the coordinator handles the decision, continue waiting from that cursor.

After a terminal event, store its cursor outside the active set and remove the target. A later review-fix cycle begins only when the coordinator supplies a new notificationCycleId and explicitly re-registers that target from the previous terminal cursor. If no reliable terminal cursor exists, reject observer re-registration as blocked-no-terminal-cursor; target-self remains authoritative.

You may only wait for or read task state and notify the coordinator. Do not read the repository, edit code, run tests, operate on Git or reviews, message implementation tasks, answer user decisions, perform acceptance, merge, deploy, synchronize a base checkout, archive tasks, or retire worktrees.
```
