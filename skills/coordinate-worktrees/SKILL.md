---
name: coordinate-worktrees
description: Coordinate persistent Codex App tasks across isolated Git worktrees, parallel or stacked merge requests or pull requests, progress steering, review handbacks, and coordinator-owned merge decisions. Use when delivery must remain user-visible, resumable, and independently reviewable, or when deciding whether work belongs in a short-lived subagent or a persistent worktree task.
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

## Establish the delivery graph

1. Read repository instructions, the approved design/spec, and the implementation plan.
2. Identify the real repository root, current dirty state, remote, base branch, and fixed base SHA. Preserve unrelated user changes.
3. Partition work by dependency and file ownership. Put overlapping files in one lane or define a merge order; do not rely on agents to reconcile concurrent shared edits.
4. Create or select an integration branch. For a multi-MR delivery, open a Draft umbrella MR from integration to the final base before implementation begins.
5. Record a ledger for every lane: scope, dependencies, App thread ID, worktree, branch, base SHA, MR target, MR URL, HEAD, tests, and status.

Creating a remote repository or changing repository visibility is external state. Do it only when the user already authorized that outcome or after confirmation.

Completion criterion: every implementation unit has one owner, an explicit base, a non-overlapping scope or merge order, and a declared verification command.

## Dispatch a persistent lane

1. Resolve the saved project with `codex_app__list_projects`.
2. Create the task with `codex_app__create_thread`, target the project, choose the native `worktree` environment, and set `startingState.branchName` to the existing integration branch or required parent branch. Prefer the App's native worktree over manual `git worktree` commands.
3. Give the task a searchable title and pin it while active.
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

- Inspect progress with `codex_app__read_thread`; use `codex_app__list_threads` only to relocate a handle.
- Send corrections with `codex_app__send_message_to_thread` when scope, branch, test evidence, or ownership drifts.
- Send baseline failures to every affected lane so workers separate pre-existing failures from regressions.
- Let the owning task implement its fixes. Do not patch its worktree from the coordinator unless ownership is explicitly transferred.
- Avoid noisy polling. Read at meaningful checkpoints: branch creation, first vertical slice, gate completion, MR creation, and requested-fix completion.
- Keep the user informed of lane state and review decisions, not raw internal chatter.

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
6. Unpin or archive completed App tasks only after their work is merged or deliberately abandoned.

Completion criterion: the final branch contains only reviewed child work, full gates reflect the integrated tree, manual checks are honestly reported, and no required MR or task remains unresolved.

## Guardrails

- Preserve the user's Git identity; never add AI or bot attribution unless requested.
- Keep commits small and repository-compliant.
- Keep secrets and credentials out of prompts, repository files, logs, and MR descriptions.
- Treat branch/MR ownership as the durable control plane; never infer durable ownership from a session or thread handle alone.
- Separate read-only observation from actions that push, merge, close, or mutate external systems.
