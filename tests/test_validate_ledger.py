import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "coordinate-worktrees"
    / "scripts"
    / "validate_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("validate_ledger", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def valid_ledger():
    return {
        "delivery": {
            "coordinator": {
                "threadId": "coordinator-new",
                "hostId": "local",
            },
            "authority": {
                "archiveTasks": {"state": "authorized", "source": "user"}
            },
            "release": {
                "activeBatchId": "release-1",
                "batches": [
                    {
                        "id": "release-1",
                        "target": "41100",
                        "deployedTarget": "41100",
                        "deployedRelease": "abc123",
                        "deploymentVerified": True,
                        "status": "deployed",
                        "preDeployGate": {"state": "passed", "evidence": ["validator"]},
                        "postDeployGate": {"state": "not-run", "evidence": []},
                    }
                ],
            },
        },
        "lanes": [
            {
                "id": "builder",
                "status": "retirement-pending",
                "task": {
                    "lifecycle": "terminal",
                    "threadId": "builder-task",
                    "hostId": "local",
                    "archiveState": "requested",
                },
                "placement": {
                    "worktreeKind": "codex-managed",
                    "retirementPolicy": "archive-app-task-after-merge",
                },
                "git": {"head": "head-builder"},
                "acceptance": {
                    "state": "accepted",
                    "acceptedHead": "head-builder",
                    "evidence": ["review"],
                },
                "notification": {
                    "coordinatorThreadId": "coordinator-old",
                    "coordinatorHostId": "local",
                },
                "releases": [
                    {
                        "batchId": "release-1",
                        "releaseDisposition": "include",
                        "dispositionReason": None,
                        "acceptedHead": "head-builder",
                        "integratedCommit": "merge-builder",
                        "integrationEvidence": ["master contains merge-builder"],
                        "deployedTarget": "41100",
                        "deployedRelease": "abc123",
                        "deploymentVerified": True,
                        "deploymentEvidence": ["release contains merge-builder"],
                    }
                ],
                "retirement": {
                    "disposition": "app-cleanup-pending",
                    "blockerReason": None,
                    "recoveryRef": "origin/builder",
                    "snapshotState": "unknown",
                },
            },
            {
                "id": "login",
                "status": "merge-ready",
                "task": {
                    "lifecycle": "ready",
                    "threadId": "login-task",
                    "hostId": "local",
                    "archiveState": "not-requested",
                },
                "placement": {
                    "worktreeKind": "codex-managed",
                    "retirementPolicy": "archive-app-task-after-merge",
                },
                "git": {"head": "head-login"},
                "acceptance": {
                    "state": "accepted",
                    "acceptedHead": "head-login",
                    "evidence": ["review-fix accepted"],
                },
                "notification": {
                    "coordinatorThreadId": "coordinator-new",
                    "coordinatorHostId": "local",
                },
                "releases": [
                    {
                        "batchId": "release-1",
                        "releaseDisposition": "defer",
                        "dispositionReason": "next release",
                        "acceptedHead": "head-login",
                        "integratedCommit": None,
                        "integrationEvidence": [],
                        "deployedTarget": None,
                        "deployedRelease": None,
                        "deploymentVerified": None,
                        "deploymentEvidence": [],
                    }
                ],
                "retirement": {
                    "disposition": None,
                    "blockerReason": None,
                    "recoveryRef": "origin/login",
                    "snapshotState": "unknown",
                },
            },
        ],
    }


class ValidateLedgerTests(unittest.TestCase):
    def issue_codes(self, ledger, phase):
        return {issue.code for issue in MODULE.validate_ledger(ledger, phase)}

    def test_valid_pre_deploy_batch(self):
        self.assertEqual(self.issue_codes(valid_ledger(), "pre-deploy"), set())

    def test_missing_disposition_and_acceptance_are_blocking(self):
        ledger = valid_ledger()
        lane = ledger["lanes"][1]
        lane["releases"] = []
        lane["acceptance"] = {"state": "not-reviewed", "acceptedHead": None}
        codes = self.issue_codes(ledger, "pre-deploy")
        self.assertIn("completed-lane-missing-release-disposition", codes)
        self.assertIn("completed-lane-not-accepted", codes)

    def test_stale_route_blocks_nonterminal_lane(self):
        ledger = valid_ledger()
        ledger["lanes"][1]["notification"]["coordinatorThreadId"] = "coordinator-old"
        self.assertIn(
            "stale-coordinator-route",
            self.issue_codes(ledger, "pre-deploy"),
        )

    def test_stale_acceptance_or_integration_evidence_blocks_release(self):
        ledger = valid_ledger()
        included = ledger["lanes"][0]
        included["git"]["head"] = "new-unreviewed-head"
        included["releases"][0]["integrationEvidence"] = []
        codes = self.issue_codes(ledger, "pre-deploy")
        self.assertIn("lane-head-changed-after-acceptance", codes)
        self.assertIn("missing-integration-evidence", codes)

    def test_post_deploy_requires_release_and_retirement_evidence(self):
        ledger = valid_ledger()
        included = ledger["lanes"][0]
        included["releases"][0]["deploymentEvidence"] = []
        included["retirement"] = {"disposition": None, "blockerReason": None}
        codes = self.issue_codes(ledger, "post-deploy")
        self.assertIn("missing-deployment-evidence", codes)
        self.assertIn("deployed-lane-missing-retirement", codes)

    def test_app_cleanup_pending_is_valid_after_archive_request(self):
        self.assertEqual(self.issue_codes(valid_ledger(), "post-deploy"), set())

    def test_archive_policy_is_not_treated_as_automatic(self):
        ledger = valid_ledger()
        included = ledger["lanes"][0]
        included["task"]["archiveState"] = "not-requested"
        self.assertIn(
            "archive-policy-not-executed",
            self.issue_codes(ledger, "post-deploy"),
        )

    def test_incomplete_coordinator_handoff_blocks_release(self):
        ledger = valid_ledger()
        ledger["delivery"]["coordinator"]["handoffs"] = [
            {
                "id": "handoff-1",
                "sourceLaneIds": ["builder", "login", "forgotten"],
                "nonterminalLaneIds": ["login"],
                "terminalLaneIds": ["builder", "forgotten"],
                "inheritedLaneIds": ["builder", "login"],
                "routingUpdates": [{"laneId": "login", "disposition": "delivered"}],
                "terminalReconciliations": [{"laneId": "builder"}],
                "state": "reconciling",
            }
        ]
        codes = self.issue_codes(ledger, "pre-deploy")
        self.assertIn("coordinator-handoff-incomplete", codes)
        self.assertIn("coordinator-handoff-lane-set-mismatch", codes)
        self.assertIn("handoff-terminal-reconciliation-missing", codes)


if __name__ == "__main__":
    unittest.main()
