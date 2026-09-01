#!/usr/bin/env python3
"""Read-only release and retirement gate for coordinate-worktrees ledgers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

RECONCILABLE_STATUSES = {
    "local-complete",
    "review",
    "merge-ready",
    "merged",
    "abandoned",
    "retirement-pending",
    "retired",
    "retained-blocked",
    "retained-permanent",
}
NONTERMINAL_TASK_STATES = {"ready", "active", "needs-attention"}
RELEASE_DISPOSITIONS = {"include", "defer", "blocked", "not-applicable"}
RELEASE_STATUSES = {
    "planning",
    "pre-deploy-ready",
    "deploying",
    "deployed",
    "post-deploy-verified",
    "blocked",
}
RETIREMENT_STATUS = {
    "manual-retired": "retired",
    "app-auto-cleaned-restorable": "retired",
    "cleanup-ready": "retirement-pending",
    "app-cleanup-pending": "retirement-pending",
    "retained-dirty": "retained-blocked",
    "retained-active": "retained-blocked",
    "retained-blocked": "retained-blocked",
    "permanent-retained": "retained-permanent",
}
BLOCKED_RETIREMENT = {"retained-dirty", "retained-active", "retained-blocked"}


class Issue(NamedTuple):
    code: str
    path: str
    message: str


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _sequence(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _present(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _record_path(lane_id: str, batch_id: str) -> str:
    return f"lanes[{lane_id}].releases[{batch_id}]"


def _settled_before(lane: dict[str, Any], batch_id: str) -> bool:
    current_head = _mapping(lane.get("git")).get("head")
    for raw_record in _sequence(lane.get("releases")):
        record = _mapping(raw_record)
        if record.get("batchId") == batch_id:
            continue
        same_head = not _present(current_head) or record.get("acceptedHead") == current_head
        if (
            record.get("releaseDisposition") == "include"
            and record.get("deploymentVerified") is True
            and same_head
        ):
            return True
        if (
            record.get("releaseDisposition") == "not-applicable"
            and _present(record.get("dispositionReason"))
            and same_head
        ):
            return True
    return False


def validate_ledger(
    payload: Any, phase: str, requested_batch_id: str | None = None
) -> list[Issue]:
    issues: list[Issue] = []

    def add(code: str, path: str, message: str) -> None:
        issues.append(Issue(code, path, message))

    if not isinstance(payload, dict):
        return [Issue("invalid-root", "$", "ledger root must be an object")]

    delivery = _mapping(payload.get("delivery"))
    if not delivery:
        add("missing-delivery", "delivery", "delivery object is required")

    raw_lanes = payload.get("lanes")
    if not isinstance(raw_lanes, list):
        add("missing-lanes", "lanes", "lanes must be an array")
    lanes = [_mapping(item) for item in _sequence(raw_lanes)]

    coordinator = _mapping(delivery.get("coordinator"))
    coordinator_thread = coordinator.get("threadId")
    coordinator_host = coordinator.get("hostId")
    if not _present(coordinator_thread) or not _present(coordinator_host):
        add(
            "missing-coordinator-address",
            "delivery.coordinator",
            "current coordinator threadId and hostId are required",
        )

    lane_ids: set[str] = set()
    for index, lane in enumerate(lanes):
        lane_id = lane.get("id")
        lane_path = f"lanes[{index}]"
        if not _present(lane_id):
            add("missing-lane-id", lane_path, "lane id is required")
            lane_id = f"#{index}"
        else:
            lane_id = str(lane_id)
            if lane_id in lane_ids:
                add("duplicate-lane-id", lane_path, f"duplicate lane id {lane_id}")
            lane_ids.add(lane_id)

        task = _mapping(lane.get("task"))
        if task.get("lifecycle") in NONTERMINAL_TASK_STATES and _present(
            task.get("threadId")
        ):
            notification = _mapping(lane.get("notification"))
            if (
                notification.get("coordinatorThreadId") != coordinator_thread
                or notification.get("coordinatorHostId") != coordinator_host
            ):
                add(
                    "stale-coordinator-route",
                    f"lanes[{lane_id}].notification",
                    "nonterminal target does not route to the current coordinator",
                )

        if task.get("lifecycle") == "terminal" and lane.get("status") not in RECONCILABLE_STATUSES:
            add(
                "terminal-lane-unreconciled",
                f"lanes[{lane_id}].status",
                "terminal task still lacks an acceptance/release lifecycle state",
            )

    handoffs = _sequence(coordinator.get("handoffs"))
    if handoffs:
        handoff = _mapping(handoffs[-1])
        handoff_id = str(handoff.get("id") or "latest")
        handoff_path = f"delivery.coordinator.handoffs[{handoff_id}]"
        source_ids = {str(item) for item in _sequence(handoff.get("sourceLaneIds"))}
        inherited_ids = {
            str(item) for item in _sequence(handoff.get("inheritedLaneIds"))
        }
        nonterminal_ids = {
            str(item) for item in _sequence(handoff.get("nonterminalLaneIds"))
        }
        terminal_ids = {
            str(item) for item in _sequence(handoff.get("terminalLaneIds"))
        }
        routing_ids = {
            str(_mapping(item).get("laneId"))
            for item in _sequence(handoff.get("routingUpdates"))
            if _present(_mapping(item).get("laneId"))
        }
        reconciled_ids = {
            str(_mapping(item).get("laneId"))
            for item in _sequence(handoff.get("terminalReconciliations"))
            if _present(_mapping(item).get("laneId"))
        }
        if handoff.get("state") != "complete":
            add(
                "coordinator-handoff-incomplete",
                f"{handoff_path}.state",
                "latest coordinator handoff must be complete before deployment",
            )
        if source_ids != inherited_ids:
            add(
                "coordinator-handoff-lane-set-mismatch",
                handoff_path,
                "sourceLaneIds and inheritedLaneIds differ",
            )
        if source_ids != nonterminal_ids | terminal_ids or nonterminal_ids & terminal_ids:
            add(
                "coordinator-handoff-partition-mismatch",
                handoff_path,
                "terminal and nonterminal lane IDs must partition sourceLaneIds",
            )
        if not inherited_ids.issubset(lane_ids):
            add(
                "inherited-lane-missing-from-ledger",
                f"{handoff_path}.inheritedLaneIds",
                "an inherited lane is absent from the destination ledger",
            )
        if not nonterminal_ids.issubset(routing_ids):
            add(
                "handoff-routing-update-missing",
                f"{handoff_path}.routingUpdates",
                "every nonterminal source lane needs a routing update or blocker record",
            )
        if not terminal_ids.issubset(reconciled_ids):
            add(
                "handoff-terminal-reconciliation-missing",
                f"{handoff_path}.terminalReconciliations",
                "every terminal source lane needs acceptance/release/retirement reconciliation",
            )

    release = _mapping(delivery.get("release"))
    batch_id = requested_batch_id or release.get("activeBatchId")
    if not _present(batch_id):
        add(
            "missing-active-release-batch",
            "delivery.release.activeBatchId",
            "active release batch id is required",
        )
        return sorted(issues)
    batch_id = str(batch_id)

    raw_batches = _sequence(release.get("batches"))
    batches = [
        _mapping(item) for item in raw_batches if _mapping(item).get("id") == batch_id
    ]
    if len(batches) != 1:
        add(
            "invalid-active-release-batch",
            "delivery.release.batches",
            f"expected exactly one batch with id {batch_id}, found {len(batches)}",
        )
        return sorted(issues)
    batch = batches[0]
    batch_path = f"delivery.release.batches[{batch_id}]"
    if not _present(batch.get("target")):
        add("missing-release-target", f"{batch_path}.target", "release target is required")
    if batch.get("status") not in RELEASE_STATUSES:
        add(
            "invalid-release-status",
            f"{batch_path}.status",
            f"release status must be one of {sorted(RELEASE_STATUSES)}",
        )

    current_records: dict[str, dict[str, Any]] = {}
    for lane in lanes:
        lane_id = str(lane.get("id"))
        matching = [
            _mapping(item)
            for item in _sequence(lane.get("releases"))
            if _mapping(item).get("batchId") == batch_id
        ]
        if len(matching) > 1:
            add(
                "duplicate-release-record",
                f"lanes[{lane_id}].releases",
                f"lane has {len(matching)} records for batch {batch_id}",
            )
        if matching:
            current_records[lane_id] = matching[0]

    for lane in lanes:
        lane_id = str(lane.get("id"))
        lane_status = lane.get("status")
        acceptance = _mapping(lane.get("acceptance"))
        accepted_head = acceptance.get("acceptedHead")
        git_head = _mapping(lane.get("git")).get("head")
        record = current_records.get(lane_id)
        record_path = _record_path(lane_id, batch_id)

        if (
            lane_status in RECONCILABLE_STATUSES
            and not _settled_before(lane, batch_id)
            and record is None
        ):
            add(
                "completed-lane-missing-release-disposition",
                record_path,
                "unsettled completed lane has no current release record",
            )
            if acceptance.get("state") != "accepted" or not _present(accepted_head):
                add(
                    "completed-lane-not-accepted",
                    f"lanes[{lane_id}].acceptance",
                    "completed lane has no coordinator-accepted HEAD",
                )
            continue

        if record is None:
            continue

        disposition = record.get("releaseDisposition")
        if disposition not in RELEASE_DISPOSITIONS:
            add(
                "invalid-release-disposition",
                f"{record_path}.releaseDisposition",
                f"disposition must be one of {sorted(RELEASE_DISPOSITIONS)}",
            )
            continue

        if disposition in {"defer", "blocked", "not-applicable"} and not _present(
            record.get("dispositionReason")
        ):
            add(
                "missing-disposition-reason",
                f"{record_path}.dispositionReason",
                f"{disposition} requires a reason",
            )

        if disposition in {"include", "defer"}:
            if acceptance.get("state") != "accepted" or not _present(accepted_head):
                add(
                    "completed-lane-not-accepted",
                    f"lanes[{lane_id}].acceptance",
                    f"{disposition} requires coordinator acceptance",
                )
            elif not _sequence(acceptance.get("evidence")):
                add(
                    "missing-acceptance-evidence",
                    f"lanes[{lane_id}].acceptance.evidence",
                    f"{disposition} requires acceptance evidence",
                )
            if _present(git_head) and _present(accepted_head) and git_head != accepted_head:
                add(
                    "lane-head-changed-after-acceptance",
                    f"lanes[{lane_id}].git.head",
                    "current lane HEAD differs from the coordinator-accepted HEAD",
                )
            if not _present(record.get("acceptedHead")):
                add(
                    "missing-release-accepted-head",
                    f"{record_path}.acceptedHead",
                    f"{disposition} requires acceptedHead",
                )
            elif _present(accepted_head) and record.get("acceptedHead") != accepted_head:
                add(
                    "accepted-head-mismatch",
                    f"{record_path}.acceptedHead",
                    "release acceptedHead differs from lane acceptance",
                )

        if disposition == "include":
            if lane_status not in RECONCILABLE_STATUSES:
                add(
                    "included-lane-not-complete",
                    f"lanes[{lane_id}].status",
                    "included lane is not in a completed lifecycle state",
                )
            if not _present(record.get("integratedCommit")):
                add(
                    "missing-integrated-commit",
                    f"{record_path}.integratedCommit",
                    "included lane requires integratedCommit before deployment",
                )
            if not _sequence(record.get("integrationEvidence")):
                add(
                    "missing-integration-evidence",
                    f"{record_path}.integrationEvidence",
                    "included lane requires current integration containment evidence",
                )

    if phase == "post-deploy":
        pre_gate = _mapping(batch.get("preDeployGate"))
        if pre_gate.get("state") != "passed":
            add(
                "pre-deploy-gate-not-recorded",
                f"{batch_path}.preDeployGate.state",
                "post-deploy validation requires a recorded passing pre-deploy gate",
            )
        if not _present(batch.get("deployedTarget")):
            add(
                "missing-batch-deployed-target",
                f"{batch_path}.deployedTarget",
                "deployed target is required after deployment",
            )
        if not _present(batch.get("deployedRelease")):
            add(
                "missing-batch-deployed-release",
                f"{batch_path}.deployedRelease",
                "immutable deployed release is required after deployment",
            )
        if batch.get("deploymentVerified") is not True:
            add(
                "batch-deployment-not-verified",
                f"{batch_path}.deploymentVerified",
                "batch deployment must be verified from current evidence",
            )

        archive_authority = _mapping(_mapping(delivery.get("authority")).get("archiveTasks"))
        for lane in lanes:
            lane_id = str(lane.get("id"))
            record = current_records.get(lane_id)
            if not record or record.get("releaseDisposition") != "include":
                continue
            record_path = _record_path(lane_id, batch_id)
            expected_target = batch.get("deployedTarget") or batch.get("target")
            if record.get("deployedTarget") != expected_target:
                add(
                    "deployed-target-mismatch",
                    f"{record_path}.deployedTarget",
                    "lane deployedTarget differs from the verified batch target",
                )
            if record.get("deployedRelease") != batch.get("deployedRelease"):
                add(
                    "deployed-release-mismatch",
                    f"{record_path}.deployedRelease",
                    "lane deployedRelease differs from the verified batch release",
                )
            if record.get("deploymentVerified") is not True:
                add(
                    "lane-deployment-not-verified",
                    f"{record_path}.deploymentVerified",
                    "included lane deployment is not verified",
                )
            if not _sequence(record.get("deploymentEvidence")):
                add(
                    "missing-deployment-evidence",
                    f"{record_path}.deploymentEvidence",
                    "included lane requires deployment evidence",
                )

            retirement = _mapping(lane.get("retirement"))
            retirement_disposition = retirement.get("disposition")
            if retirement_disposition not in RETIREMENT_STATUS:
                add(
                    "deployed-lane-missing-retirement",
                    f"lanes[{lane_id}].retirement.disposition",
                    "deployed lane requires a recognized retirement disposition",
                )
            else:
                expected_status = RETIREMENT_STATUS[retirement_disposition]
                if lane.get("status") != expected_status:
                    add(
                        "retirement-status-mismatch",
                        f"lanes[{lane_id}].status",
                        f"{retirement_disposition} requires lane status {expected_status}",
                    )
                if retirement_disposition in BLOCKED_RETIREMENT and not _present(
                    retirement.get("blockerReason")
                ):
                    add(
                        "missing-retirement-blocker",
                        f"lanes[{lane_id}].retirement.blockerReason",
                        f"{retirement_disposition} requires a precise blocker",
                    )

            placement = _mapping(lane.get("placement"))
            policy = placement.get("retirementPolicy")
            task = _mapping(lane.get("task"))
            if isinstance(policy, str) and policy.startswith("archive-app-task"):
                archive_state = task.get("archiveState")
                if archive_authority.get("state") == "authorized":
                    if archive_state not in {"requested", "archived", "verification-failed"}:
                        add(
                            "archive-policy-not-executed",
                            f"lanes[{lane_id}].task.archiveState",
                            "archive policy is not automation; authorized archive was not requested",
                        )
                elif not _present(retirement.get("blockerReason")):
                    add(
                        "archive-authority-unresolved",
                        f"lanes[{lane_id}].retirement.blockerReason",
                        "archive policy lacks authority and an explicit blocker",
                    )

            if retirement_disposition == "app-cleanup-pending" and task.get(
                "archiveState"
            ) not in {"requested", "verification-failed"}:
                add(
                    "cleanup-pending-without-archive-request",
                    f"lanes[{lane_id}].task.archiveState",
                    "app-cleanup-pending requires an archive request or failed read-back",
                )

    return sorted(issues)


def _load_payload(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a coordinate-worktrees JSON ledger without modifying it."
    )
    parser.add_argument("ledger", help="JSON ledger path, or - for standard input")
    parser.add_argument(
        "--phase", required=True, choices=("pre-deploy", "post-deploy")
    )
    parser.add_argument("--batch-id", help="release batch id; defaults to activeBatchId")
    args = parser.parse_args(argv)

    try:
        payload = _load_payload(args.ledger)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR unable to read ledger: {exc}", file=sys.stderr)
        return 2

    issues = validate_ledger(payload, args.phase, args.batch_id)
    if issues:
        print(f"FAIL phase={args.phase} issues={len(issues)}")
        for issue in issues:
            print(f"{issue.code}\t{issue.path}\t{issue.message}")
        return 1

    print(f"PASS phase={args.phase} batch={args.batch_id or _mapping(_mapping(payload.get('delivery')).get('release')).get('activeBatchId')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
