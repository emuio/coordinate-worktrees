# Project Task Listener

Use one optional listener per project when several App tasks or long-running tasks make direct coordination noisy, or when the user explicitly asks for low-cost monitoring. A single short task should normally stay on direct coordinator `wait_threads` calls.

## Create and classify the listener

- Resolve the saved project for the delivery graph from the current invocation entry point. Record the exact project path, `projectKind`, and `hostId` returned by that call, plus the invocation entry point and observation time. A matching path or project name does not prove that another entry point will select the same host.
- If the user requested event-driven monitoring, explain the observed host's monitoring implications before creating the target. Prefer a currently returned local project route for future target and listener creation when it is available and the user has not explicitly chosen remote or mobile execution. This preference does not migrate the existing coordinator or any existing target to another host. Do not override an explicit remote or mobile choice.
- After target creation and before announcing a listener as active, make one capability probe with `wait_threads`, the target's actual `threadId` and `hostId`, and `timeoutMs: 0`. A supported nonterminal snapshot or timeout means the handler route is available; it does not mean the target completed. Do not classify a route from `projectKind` or `hostId` alone.
- When the probe succeeds, create or reuse the listener under the selected project route and title it `<project-name> 任务监听器`; the coordinator task itself may remain unassociated when it predates project-scoped coordination. For a Git saved project, call `create_thread` with the non-worktree `environment: {type: "local"}` as the project classification surface. Here `environment.type: local` selects the listener's non-worktree execution mode; it does not mean `projectKind=local`, force `hostId=local`, or replace the selected project/host route. The listener remains strictly read-only even when its working directory exposes the repository.
- When the probe reports `No handler registered for tool: codex_app.wait_threads` or an equivalent unsupported target-host route, set `listenerLifecycle` to `listener-unsupported-target-host`. Do not create or recreate a listener for that target, use fixed polling, repeatedly call `read_thread`, or claim monitoring is active. Instead, append the direct self-notification fallback below to the target once and record the degraded route.
- Give it a self-contained observer brief. It is independent and does not inherit the coordinator's repository or business context.
- Monitor only tasks from that project. Keep at most eight active targets in one project listener; leave overflow with the coordinator or an explicitly separate project-scoped listener rather than mixing projects.
- Use projectless only when no saved project exists, or for temporary cross-project observation after the user explicitly accepts mixed classification. Never make that fallback a project's default or silently reuse it across projects.

Project titles and association improve discovery in the App. They do not replace durable branch, MR or PR, and ledger ownership.

## Choose listener model and reasoning

Treat `model` and reasoning (`thinking`) as independent settings. Setting `thinking: low` does not select a lower-cost model; omitting `model` still uses the task's configured default model.

- If the user did not choose overrides, follow the entrypoint's **Choose model and reasoning settings** rule and use configured defaults.
- If the user explicitly requests a low-cost listener, resolve an available efficient model under that same choice rule and set both the chosen model and `thinking: low` explicitly. Honor an explicit model choice when available, but do not hardcode one model as the default for every project.
- A later, explicitly authorized settings change applies to subsequent listener turns only. It does not require stopping or changing the implementation tasks being observed.
- Record the effective model and reasoning separately, with the source of each value.

## Preserve the read-only boundary

The listener may only wait for or read task state and send one logical completion or attention notification per observed event to that project's coordinator. It must not read the repository, edit code, run tests, inspect or operate on Git or an MR or PR, deploy, perform acceptance, merge, synchronize the base checkout, retire worktrees, message implementation tasks, or answer on the user's behalf.

The coordinator retains handoff reading, partitioning, dispatch, ledger maintenance, steering, independent acceptance, test reruns, diff review, merge decisions or authorization requests, deployment, base synchronization, and worktree retirement. A listener report is a routing signal, not acceptance evidence.

## Maintain the observer ledger

Record the listener outside the Git lane list with:

- `coordinatorTitle`, exact `coordinatorThreadId`, `coordinatorHostId`, and `coordinatorProjectId` (including an explicit empty value);
- project-resolution snapshot: project path, `projectKind`, `hostId`, invocation entry point, and observation time;
- probe target `threadId` and `hostId`, probe result, and probe time;
- `listenerEnvironmentType: local` for the non-worktree `create_thread` mode, recorded separately from project `projectKind` and `hostId`;
- `listenerThreadId`, `listenerProjectId`, its `hostId`, effective `model` and `reasoning`, plus `modelSource` and `reasoningSource`, when a listener exists;
- active targets as task name, `threadId`, `hostId`, and latest cursor;
- `listenerLifecycle`, such as `creating`, `active-wait`, `listener-unsupported-target-host`, `migration-pending`, `superseded-retained`, or `archived`;
- for a degraded route, `notificationFallback: direct-self-notification`, the fallback message attempt, and whether its terminal or attention notification was delivered, retried once, or remains undelivered.

## Follow the event-driven protocol

1. Give the listener the coordinator task's title, exact `threadId` and `hostId`, and its `projectId` when present; record the project ID as empty when the existing coordinator is unassociated. The exact thread and host are the notification address—never infer the destination from title or project association. Add each initial target's task name, `threadId`, `hostId`, and latest cursor when one exists.
2. Maintain an active target set and cursor per target. Treat later target messages as additive: add same-project targets without discarding active ones. Remove, pause, or replace a nonterminal target only when the message explicitly names it and requests that lifecycle change. Do not add a ninth active target or a target from another project.
3. Call `wait_threads` with the active targets and their latest cursors. A new message may end the current wait early; after handling it, rebuild the active target and cursor map and resume the event wait. Do not emit fixed-period heartbeats, repeatedly call `read_thread`, or narrate unchanged state. Use `read_thread` only if the wait result lacks the final summary needed for the permitted notification.
4. On completion, send the coordinator only the task name, `threadId`, terminal status, and final summary. On a blocker or request for input, send only a minimal attention notice with the task name, `threadId`, status, and requested decision. Never send progress chatter or perform acceptance.
5. Each completion or attention notice is one logical notification. A failed or timed-out `send_message_to_thread` call does not prove delivery; retry at most once as transport recovery. If the retry also fails or times out, state clearly in the listener task that the notification was not delivered and never record it as delivered.
6. After a terminal status, complete the notification attempt and remove that target. Continue waiting for the remaining active targets. When none remain, stay available for later same-project targets without inventing a heartbeat schedule.

## Migrate a projectless listener

Do not claim that an existing task's `projectId` can be changed in place.

Likewise, returning to the desktop or another invocation entry point only affects later `list_projects` and `create_thread` choices. It does not migrate an existing remote target, change its host, or make an unsupported listener route active. Re-resolve the project and repeat the one-shot capability probe for each newly created target because host capabilities may change; do not hardcode mobile, remote, slingshot, or any other host as permanently unsupported.

1. Resolve the saved project and create a new project-associated, read-only listener on a currently capability-proven route with the recommended title. For a Git saved project, use the non-worktree `environment: {type: "local"}` without treating that environment type as `hostId=local`.
2. Give it the same `coordinatorThreadId` and the coordinator/project/host details, then migrate any active target handles and latest cursors. An already completed old listener may have no active targets; record that empty set instead of inventing a migration.
3. Add the current same-project targets and confirm from the new listener's task state that it registered them and entered `active-wait` before declaring the migration active.
4. Tell an active old projectless listener to drop migrated targets and record it as `superseded-retained`. If it is already complete with no targets, record that observed state. If overlap cannot be eliminated, record it and deduplicate notifications at the coordinator.
5. Archive the old listener only when retirement authorization already exists or is newly obtained, and only after the new listener reaches `active-wait`. Record both lifecycle states; do not equate migration with archive authorization.

## Reusable project listener prompt

Create the task under the currently selected and capability-proven `<PROJECT_ID>` route with the non-worktree `environment: {type: "local"}` and title it `<PROJECT_NAME> 任务监听器`. This `local` value is the `create_thread` environment type, not the project's `projectKind` or `hostId`; it does not force the selected host route to local. Replace the placeholders and add targets using the same four-field shape.

```text
You are an independent, project-associated, strictly read-only Codex App task listener. Project association is only for discoverability; you are not a Git delivery lane and do not inherit the coordinator's repository or business context.

Project classification:
- project name: <PROJECT_NAME>
- projectId: <PROJECT_ID>
- project path: <PROJECT_PATH>
- projectKind: <PROJECT_KIND_FROM_CURRENT_LIST_PROJECTS>
- project hostId: <PROJECT_HOST_ID_FROM_CURRENT_LIST_PROJECTS>
- resolution entry point: <CURRENT_INVOCATION_ENTRY_POINT>
- listener environment type: local (non-worktree; separate from projectKind and hostId)

Notify only this project coordinator:
- coordinator title: <COORDINATOR_TITLE>
- coordinator threadId: <COORDINATOR_THREAD_ID>
- coordinator projectId: <COORDINATOR_PROJECT_ID_OR_NONE>
- coordinator hostId: <COORDINATOR_HOST_ID>

Use the exact coordinator threadId and hostId above for notifications. Never infer the destination from its title or projectId.

Listener settings and provenance:
- model: <EFFECTIVE_MODEL>
- model source: <CONFIGURED_DEFAULT_OR_EXPLICIT_USER_CHOICE>
- reasoning: <EFFECTIVE_REASONING>
- reasoning source: <CONFIGURED_DEFAULT_OR_EXPLICIT_USER_CHOICE>

Initial active targets:
- task name: <TASK_NAME>
  threadId: <TARGET_THREAD_ID>
  hostId: <TARGET_HOST_ID>
  cursor: <LATEST_CURSOR_OR_NONE>

Observe only with event-driven wait_threads calls. Keep the latest cursor per target, pass cursors into later waits, and keep at most eight active targets. Do not use a fixed-period heartbeat or repeatedly call read_thread. A wait timeout is not completion; re-enter the event wait with current cursors and do not narrate unchanged state.

Later messages are additive by default. Append targets from this same project without dropping active targets; reject cross-project targets and do not add a ninth active target. Remove, pause, or replace a nonterminal target only when a message explicitly names it and requests that lifecycle change. A new message may end the current wait early, so rebuild the active target and cursor map after handling it and resume waiting. After a terminal status, complete the notification attempt, remove that target, and continue observing the rest.

You may only wait for or read task state and notify the coordinator. Do not read the repository, edit code, run tests, inspect or operate on Git or an MR or PR, deploy, perform acceptance, merge, synchronize a base checkout, retire a worktree, message implementation tasks, or answer blockers or input requests on the user's behalf.

When a target completes, use send_message_to_thread to send the coordinator only:
- task name
- threadId
- terminal status
- final summary

When a target is blocked or requests input, send only a minimal attention notice with task name, threadId, status, and requested decision. Each event gets one logical notification. A send failure or timeout is not delivery; retry at most once, then clearly report undelivered status in this listener task and do not claim otherwise.

Model and reasoning are independent: low reasoning does not select a lower-cost model. Apply only settings authorized under the coordinator's model-choice rule. A later authorized change affects subsequent listener turns, not the implementation tasks being observed. The coordinator independently validates all results and retains review, merge, deployment, base synchronization, and worktree retirement authority.
```

## Reusable direct self-notification fallback

Use this only after the one-shot capability probe classifies the target as `listener-unsupported-target-host`. Send it once to the existing target; do not create a replacement target or listener. This fallback routes the target's own terminal or attention state and is not event-driven observation.

```text
The coordinator could not register event-driven wait_threads monitoring for this task's current host. Do not change execution host, create a listener, poll another task, or claim that monitoring is active.

Notify only this coordinator when your own task reaches a terminal state or needs attention:
- coordinator title: <COORDINATOR_TITLE>
- coordinator threadId: <COORDINATOR_THREAD_ID>
- coordinator hostId: <COORDINATOR_HOST_ID>

For completion, send only your task name, threadId, `completed`, and final summary. For a blocker or input request, send only your task name, threadId, `blocked` or `needs_attention`, and the requested decision. Each state gets one logical notification. If `send_message_to_thread` fails or times out, retry at most once; if that retry also fails, report the notification as undelivered in your own task and do not claim delivery.

This routing permission does not authorize you to inspect or accept other tasks, perform independent acceptance, merge, deploy, synchronize a base checkout, retire worktrees, or expand your assigned scope. The coordinator retains all acceptance and lifecycle authority.
```
