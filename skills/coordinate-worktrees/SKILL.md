---
name: coordinate-worktrees
description: Coordinate persistent Codex App tasks across isolated Git worktrees, parallel or stacked merge requests or pull requests, progress steering, review handbacks, coordinator-owned merge decisions, and safe lane retirement. Use when delivery must remain user-visible, resumable, and independently reviewable, when deciding whether work belongs in a short-lived subagent or persistent worktree task, or when safely cleaning up completed worktrees and branches.
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

## Choose model and reasoning settings

Choose the execution surface first; model and reasoning settings are a secondary decision. Do not present automatic difficulty-based model routing as a Codex default.

| Surface | Default behavior | Coordinator rule |
| --- | --- | --- |
| Full-history collaboration subagent | Inherits the parent task's current model and reasoning effort | Keep inheritance unless the user, applicable instructions, or the selected skill explicitly requires an override and the spawn form permits it |
| New Codex App task | Uses configured defaults when model and reasoning overrides are omitted; it does not inherit the coordinator task's transient settings | Do not silently pin or change settings; when the choice materially affects the work, state the expected default and obtain an explicit choice before overriding it |

Record the model, reasoning effort, and their source when known: inherited, configured default, or explicitly pinned. Do not add project or global custom agents merely to route persistent App tasks; those tasks have their own configuration path.

## Establish the delivery graph

1. Read repository instructions, the approved design/spec, and the implementation plan.
2. Identify the real repository root, current dirty state, remote, base branch, and fixed base SHA. Preserve unrelated user changes.
3. Partition work by dependency and file ownership. Put overlapping files in one lane or define a merge order; do not rely on agents to reconcile concurrent shared edits.
4. Create or select an integration branch. For a multi-MR delivery, open a Draft umbrella MR from integration to the final base before implementation begins.
5. Record a ledger for every lane: scope, dependencies, execution surface, model and reasoning source when known, App thread ID, worktree, branch, base SHA, MR target, MR URL, HEAD, tests, and status.

Creating a remote repository or changing repository visibility is external state. Do it only when the user already authorized that outcome or after confirmation.

Completion criterion: every implementation unit has one owner, an explicit base, a non-overlapping scope or merge order, and a declared verification command.

## Dispatch a persistent lane

1. Resolve the saved project with `codex_app__list_projects`.
2. Create the task with `codex_app__create_thread`, target the project, choose the native `worktree` environment, and set `startingState.branchName` to the existing integration branch or required parent branch. Prefer the App's native worktree over manual `git worktree` commands.
   Unless the user explicitly selected a model or reasoning level, leave those overrides unset so the task uses configured defaults.
3. Give the task a searchable title. Leave it unpinned unless the user explicitly requests pinning; do not use sidebar order as coordination state.
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

- Follow progress with bounded `wait_threads` calls. Use one call for one to eight targets, pass each target's latest cursor, and use `timeoutMs: 0` for an immediate compact snapshot.
- Use `read_thread` only when the full transcript or diagnostic detail is required; use `list_threads` only to relocate a handle.
- Send corrections with `codex_app__send_message_to_thread` when scope, branch, test evidence, or ownership drifts.
- Send baseline failures to every affected lane so workers separate pre-existing failures from regressions.
- Let the owning task implement its fixes. Do not patch its worktree from the coordinator unless ownership is explicitly transferred.
- Wait at meaningful checkpoints: branch creation, first vertical slice, gate completion, MR creation, and requested-fix completion. Do not narrate unchanged snapshots or answer approval and user-input requests on behalf of the user.
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
6. Retire completed lanes only after their work is merged or deliberately abandoned, following the safety checks below.

Completion criterion: the final branch contains only reviewed child work, full gates reflect the integrated tree, manual checks are honestly reported, and no required MR or task remains unresolved.

## Retire completed lanes safely

1. Resolve the lane from the ledger. Record its owner, App task, absolute worktree path, branch, HEAD, MR, target branch, and whether the worktree is App-managed or manual.
2. Verify retirement with read-only evidence:
   - the MR is merged, or abandonment is explicit and its HEAD is preserved on a recoverable remote ref;
   - the target branch contains the intended HEAD or merge commit;
   - the owning task is no longer running;
   - `git worktree list --porcelain` maps the exact path to the expected branch and HEAD;
   - `git -C <absolute-worktree-path> status --porcelain` is empty.
3. Stop and report instead of cleaning when the path, branch, or HEAD differs from the ledger; the worktree is dirty; the branch is unmerged or unpushed; another task owns it; or abandonment would discard unrecoverable work.
4. For an App-managed worktree, archive the task after verification when retirement is authorized. Do not change its pin state unless the user explicitly requests it. Do not assume archiving removes the physical worktree, and do not manually remove a worktree still owned by Codex App. Use an App-provided lifecycle or handoff operation when available; otherwise leave physical cleanup to the App and record that state.
5. For a coordinator-owned manual worktree, remove only the verified absolute path with `git worktree remove <absolute-worktree-path>`, then run `git worktree prune`. Never use a glob, unresolved variable, broad parent directory, `rm -rf`, or `git worktree remove --force` as the default cleanup path.
6. Delete a local lane branch only after its merged state is verified. Delete a remote branch only when repository policy or explicit user authorization permits it. Retire an integration branch only after the umbrella MR is merged and no open child MR still targets it.
7. Mark the ledger entry `retired` and record the merge or preservation ref, task archive state, worktree disposition, branch disposition, and cleanup timestamp.

Completion criterion: all retired work remains recoverable from the merged target or recorded remote ref, no dirty or actively owned worktree was removed, and the ledger matches the remaining App tasks, worktrees, and branches.

## Guardrails

- Preserve the user's Git identity; never add AI or bot attribution unless requested.
- Keep commits small and repository-compliant.
- Keep secrets and credentials out of prompts, repository files, logs, and MR descriptions.
- Treat branch/MR ownership as the durable control plane; never infer durable ownership from a session or thread handle alone.
- Separate read-only observation from actions that push, merge, close, or mutate external systems.
- Never trade cleanup convenience for recoverability; leave uncertain lanes in place and report the exact blocking evidence.
