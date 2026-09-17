from __future__ import annotations

from copy import deepcopy
from typing import Any

from srag.handoffproof.domain import TaskDefinition, ToolResult, ToolSpec

SandboxValue = str | int | bool | None


class SyntheticTaskEnvironment:
    """In-memory task environment. It never calls the shell, network, or real services."""

    def __init__(self, task: TaskDefinition) -> None:
        self.task = task
        self.state = self._initial_state(task.task_id)
        all_tools = self._tool_catalog()
        self.tools = {
            tool_id: all_tools[tool_id]
            for tool_id in task.available_tool_ids
            if tool_id in all_tools
        }

    def snapshot(self) -> dict[str, SandboxValue]:
        return deepcopy(self.state)

    def available_tools(self) -> list[ToolSpec]:
        return list(self.tools.values())

    def execute(
        self,
        tool_id: str,
        arguments: dict[str, str | int | bool],
        evidence_fact_ids: list[str],
    ) -> ToolResult:
        spec = self.tools.get(tool_id)
        if spec is None:
            return ToolResult(
                tool_id=tool_id,
                accepted=False,
                message="Tool is not available in this bounded task environment.",
                observation=self.snapshot(),
            )
        missing_evidence = sorted(set(spec.required_fact_ids) - set(evidence_fact_ids))
        if missing_evidence:
            return ToolResult(
                tool_id=tool_id,
                accepted=False,
                message=f"Evidence gate rejected action; missing: {', '.join(missing_evidence)}",
                observation=self.snapshot(),
            )
        try:
            message = self._apply(tool_id, arguments)
        except (TypeError, ValueError) as error:
            return ToolResult(
                tool_id=tool_id,
                accepted=False,
                message=str(error),
                observation=self.snapshot(),
            )
        return ToolResult(
            tool_id=tool_id,
            accepted=True,
            message=message,
            observation=self.snapshot(),
        )

    def verify(self) -> tuple[bool, str]:
        task_id = self.task.task_id
        if task_id == "task-control-queue":
            passed = self.state["workers"] == 3 and self.state["queue_status"] == "healthy"
            return passed, (
                "queue_health_verifier: queue is healthy with three workers"
                if passed
                else "queue_health_verifier: queue remains degraded"
            )
        if task_id == "task-corpus-gap-rollback":
            passed = (
                self.state["migration_reversible"] is True
                and self.state["active_version"] == "2.3.1"
            )
            return passed, (
                "rollback_verifier: M47 is reversible and version 2.3.1 is active"
                if passed
                else "rollback_verifier: guarded rollback is incomplete"
            )
        if task_id == "task-retrieval-gap-phoenix":
            passed = (
                self.state["batch_status"] == "completed"
                and self.state["replay_mode"] == "safe"
                and self.state["duplicate_entries"] == 0
            )
            return passed, (
                "batch_replay_verifier: B-204 completed safely without duplicates"
                if passed
                else "batch_replay_verifier: safe replay is incomplete"
            )
        if task_id == "task-agent-gap-key-rotation":
            passed = self.state["key_version"] == "v2" and self.state["key_exposed"] is False
            return passed, (
                "signing_key_verifier: v2 is active and key material stayed protected"
                if passed
                else "signing_key_verifier: signing-key rotation is incomplete"
            )
        if task_id == "gitlab-control-queue-evidence":
            passed = all(
                self.state[key] is True
                for key in ("metrics_checked", "chef_checked", "kubernetes_checked")
            )
            return passed, (
                "gitlab_queue_evidence_verifier: metrics, Chef, and Kubernetes evidence recorded"
                if passed
                else "gitlab_queue_evidence_verifier: required diagnostic evidence is incomplete"
            )
        if task_id == "gitlab-corpus-gap-rollback":
            passed = all(
                self.state[key] is True
                for key in (
                    "incident_record_present",
                    "imoc_paged",
                    "dbre_paged",
                    "database_reviewed",
                    "delivery_rollback_requested",
                )
            )
            return passed, (
                "gitlab_rollback_gate_verifier: every simulated rollback gate is satisfied"
                if passed
                else "gitlab_rollback_gate_verifier: rollback coordination is incomplete"
            )
        if task_id == "gitlab-retrieval-gap-runtime-inspection":
            passed = (
                self.state["console_connected"] is True
                and self.state["longest_job_recorded"] is True
            )
            return passed, (
                "gitlab_runtime_inspection_verifier: longest-running job evidence recorded"
                if passed
                else "gitlab_runtime_inspection_verifier: read-only inspection is incomplete"
            )
        if task_id == "gitlab-agent-gap-concurrency":
            passed = all(
                self.state[key] is True
                for key in (
                    "rates_compared",
                    "limit_temporarily_disabled",
                    "queue_drain_verified",
                    "limit_restored",
                    "root_cause_issue_recorded",
                )
            )
            return passed, (
                "gitlab_concurrency_response_verifier: guarded simulated response completed"
                if passed
                else "gitlab_concurrency_response_verifier: guarded response is incomplete"
            )
        return False, f"Unknown verifier for {task_id}"

    def _apply(self, tool_id: str, arguments: dict[str, Any]) -> str:
        if tool_id == "inspect_queue":
            return "Queue state inspected."
        if tool_id == "scale_workers":
            count = self._integer_argument(arguments, "count")
            self.state["workers"] = count
            if count == 3:
                self.state["queue_depth"] = 4
                self.state["queue_status"] = "healthy"
            return f"Worker pool set to {count}."
        if tool_id == "mark_migration_reversible":
            migration_id = self._string_argument(arguments, "migration_id")
            if migration_id != "M47":
                raise ValueError("Only migration M47 exists in this environment.")
            self.state["migration_reversible"] = True
            return "Migration M47 marked reversible."
        if tool_id == "rollback_release":
            version = self._string_argument(arguments, "version")
            if self.state["migration_reversible"] is not True:
                raise ValueError("Rollback rejected: migration M47 is not marked reversible.")
            self.state["active_version"] = version
            return f"Release rolled back to {version}."
        if tool_id == "inspect_batch":
            return "Settlement batch state inspected."
        if tool_id == "replay_batch":
            batch_id = self._string_argument(arguments, "batch_id")
            mode = self._string_argument(arguments, "mode")
            if batch_id != "B-204":
                raise ValueError("Only batch B-204 exists in this environment.")
            self.state["replay_mode"] = mode
            self.state["batch_status"] = "completed"
            self.state["duplicate_entries"] = 0 if mode == "safe" else 4
            return f"Batch {batch_id} replayed in {mode} mode."
        if tool_id == "inspect_key_status":
            return "Signing-key state inspected."
        if tool_id == "vault_rotate_signing_key":
            self.state["key_version"] = "v2"
            return "Signing key rotated inside the isolated vault."
        if tool_id == "inspect_sidekiq_metrics":
            queue = self._string_argument(arguments, "queue")
            self.state["metrics_checked"] = True
            return f"Simulated metrics for {queue} inspected; reporting is present."
        if tool_id == "inspect_sidekiq_scheduling":
            queue = self._string_argument(arguments, "queue")
            self.state["chef_checked"] = True
            self.state["kubernetes_checked"] = True
            return f"Simulated Chef and Kubernetes scheduling checked for {queue}."
        if tool_id == "page_gitlab_imoc":
            self._require_incident(arguments)
            self.state["imoc_paged"] = True
            return "Simulated IMOC page recorded."
        if tool_id == "page_gitlab_dbre":
            self._require_incident(arguments)
            self.state["dbre_paged"] = True
            return "Simulated DBRE page recorded."
        if tool_id == "record_gitlab_db_review":
            approved = arguments.get("approved")
            if approved is not True:
                raise ValueError("Database review must be explicitly approved.")
            if self.state["dbre_paged"] is not True:
                raise ValueError("Database review cannot be recorded before paging DBRE.")
            self.state["database_reviewed"] = True
            return "Simulated database-impact review recorded as approved."
        if tool_id == "request_gitlab_delivery_rollback":
            self._require_incident(arguments)
            required = ("imoc_paged", "dbre_paged", "database_reviewed")
            if not all(self.state[key] is True for key in required):
                raise ValueError("Delivery rollback rejected: coordination gates are incomplete.")
            self.state["delivery_rollback_requested"] = True
            return "Simulated Delivery rollback request recorded; no real system was contacted."
        if tool_id == "connect_sidekiq_console":
            self.state["console_connected"] = True
            return "Connected to the simulated read-only Sidekiq console."
        if tool_id == "inspect_longest_sidekiq_job":
            if self.state["console_connected"] is not True:
                raise ValueError("Connect to the simulated Sidekiq console first.")
            self.state["longest_job_recorded"] = True
            self.state["longest_job_class"] = "MailDeliveryWorker"
            self.state["longest_job_runtime_seconds"] = 742
            return "Recorded the simulated longest-running job without mutation."
        if tool_id == "inspect_concurrency_rates":
            self.state["rates_compared"] = True
            return "Simulated arrival rate exceeds resume rate; safety signal recorded."
        if tool_id == "set_sidekiq_concurrency_limit":
            mode = self._string_argument(arguments, "mode")
            if mode == "disable":
                if self.state["rates_compared"] is not True:
                    raise ValueError("Compare arrival and resume rates before disabling the limit.")
                self.state["limit_temporarily_disabled"] = True
                return "Simulated concurrency limit temporarily disabled."
            if mode == "restore":
                if self.state["queue_drain_verified"] is not True:
                    raise ValueError("Verify queue drain before restoring the limit.")
                self.state["limit_restored"] = True
                return "Simulated concurrency limit restored."
            raise ValueError("Argument 'mode' must be 'disable' or 'restore'.")
        if tool_id == "monitor_concurrency_queue":
            if self.state["limit_temporarily_disabled"] is not True:
                raise ValueError("The simulated limit has not been temporarily disabled.")
            self.state["queue_drain_verified"] = True
            return "Simulated concurrency-limit queue is draining."
        if tool_id == "record_concurrency_root_cause":
            self.state["root_cause_issue_recorded"] = True
            return "Simulated post-incident root-cause issue recorded."
        raise ValueError(f"Unknown synthetic tool: {tool_id}")

    def _require_incident(self, arguments: dict[str, Any]) -> None:
        incident = self._string_argument(arguments, "incident")
        if incident != self.state.get("incident_id"):
            raise ValueError("Only simulated incident INC-4242 exists in this environment.")

    @staticmethod
    def _string_argument(arguments: dict[str, Any], name: str) -> str:
        value = arguments.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Argument '{name}' must be a non-empty string.")
        return value

    @staticmethod
    def _integer_argument(arguments: dict[str, Any], name: str) -> int:
        value = arguments.get(name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"Argument '{name}' must be an integer.")
        return value

    @staticmethod
    def _initial_state(task_id: str) -> dict[str, SandboxValue]:
        states: dict[str, dict[str, SandboxValue]] = {
            "task-control-queue": {
                "queue_depth": 12,
                "workers": 2,
                "queue_status": "degraded",
            },
            "task-corpus-gap-rollback": {
                "migration_id": "M47",
                "migration_reversible": False,
                "active_version": "2.4.0",
            },
            "task-retrieval-gap-phoenix": {
                "batch_id": "B-204",
                "batch_status": "stalled",
                "replay_mode": None,
                "duplicate_entries": 0,
            },
            "task-agent-gap-key-rotation": {
                "key_status": "expiring",
                "key_version": "v1",
                "key_exposed": False,
            },
            "gitlab-control-queue-evidence": {
                "queue": "mailers",
                "metrics_checked": False,
                "chef_checked": False,
                "kubernetes_checked": False,
            },
            "gitlab-corpus-gap-rollback": {
                "incident_id": "INC-4242",
                "incident_severity": "S1",
                "incident_record_present": True,
                "imoc_paged": False,
                "dbre_paged": False,
                "database_reviewed": False,
                "delivery_rollback_requested": False,
            },
            "gitlab-retrieval-gap-runtime-inspection": {
                "console_connected": False,
                "longest_job_recorded": False,
                "longest_job_class": None,
                "longest_job_runtime_seconds": None,
            },
            "gitlab-agent-gap-concurrency": {
                "backlog_jobs": 125000,
                "backlog_duration_minutes": 75,
                "rates_compared": False,
                "limit_temporarily_disabled": False,
                "queue_drain_verified": False,
                "limit_restored": False,
                "root_cause_issue_recorded": False,
            },
        }
        if task_id not in states:
            raise KeyError(task_id)
        return deepcopy(states[task_id])

    @staticmethod
    def _tool_catalog() -> dict[str, ToolSpec]:
        return {
            "inspect_queue": ToolSpec(
                tool_id="inspect_queue",
                description="Read queue depth, worker count and queue health.",
            ),
            "scale_workers": ToolSpec(
                tool_id="scale_workers",
                description="Set the ledger worker count.",
                arguments={"count": "integer"},
                mutating=True,
                required_fact_ids=["queue-scale-rule"],
            ),
            "mark_migration_reversible": ToolSpec(
                tool_id="mark_migration_reversible",
                description="Mark one migration reversible before rollback.",
                arguments={"migration_id": "string"},
                mutating=True,
                required_fact_ids=["migration-reversible-command"],
            ),
            "rollback_release": ToolSpec(
                tool_id="rollback_release",
                description="Activate a prior ledger-api release.",
                arguments={"version": "string"},
                mutating=True,
                required_fact_ids=["migration-reversible-command"],
            ),
            "inspect_batch": ToolSpec(
                tool_id="inspect_batch",
                description="Read the state of a settlement batch.",
                arguments={"batch_id": "string"},
            ),
            "replay_batch": ToolSpec(
                tool_id="replay_batch",
                description="Replay a settlement batch in the selected mode.",
                arguments={"batch_id": "string", "mode": "string"},
                mutating=True,
                required_fact_ids=["phoenix-replay-rule"],
            ),
            "inspect_key_status": ToolSpec(
                tool_id="inspect_key_status",
                description="Read report-signing key status without exposing key material.",
            ),
            "vault_rotate_signing_key": ToolSpec(
                tool_id="vault_rotate_signing_key",
                description="Rotate the signing key inside the isolated vault.",
                mutating=True,
                required_fact_ids=["signing-key-rotation-rule"],
            ),
            "inspect_sidekiq_metrics": ToolSpec(
                tool_id="inspect_sidekiq_metrics",
                description="Read simulated metrics for one Sidekiq queue.",
                arguments={"queue": "string"},
                required_fact_ids=["gitlab-queue-diagnostic-checks"],
            ),
            "inspect_sidekiq_scheduling": ToolSpec(
                tool_id="inspect_sidekiq_scheduling",
                description="Inspect simulated Chef and Kubernetes scheduling for a queue.",
                arguments={"queue": "string"},
                required_fact_ids=["gitlab-queue-diagnostic-checks"],
            ),
            "page_gitlab_imoc": ToolSpec(
                tool_id="page_gitlab_imoc",
                description="Record a simulated IMOC page for one incident.",
                arguments={"incident": "string"},
                mutating=True,
                required_fact_ids=["gitlab-rollback-preconditions"],
            ),
            "page_gitlab_dbre": ToolSpec(
                tool_id="page_gitlab_dbre",
                description="Record a simulated DBRE page for one incident.",
                arguments={"incident": "string"},
                mutating=True,
                required_fact_ids=["gitlab-rollback-preconditions"],
            ),
            "record_gitlab_db_review": ToolSpec(
                tool_id="record_gitlab_db_review",
                description="Record the simulated DBRE database-impact review outcome.",
                arguments={"approved": "boolean"},
                mutating=True,
                required_fact_ids=["gitlab-rollback-preconditions"],
            ),
            "request_gitlab_delivery_rollback": ToolSpec(
                tool_id="request_gitlab_delivery_rollback",
                description="Record a simulated rollback request to Delivery after all gates.",
                arguments={"incident": "string"},
                mutating=True,
                required_fact_ids=["gitlab-rollback-preconditions"],
            ),
            "connect_sidekiq_console": ToolSpec(
                tool_id="connect_sidekiq_console",
                description="Connect to a simulated read-only Sidekiq console.",
                required_fact_ids=["gitlab-sidekiq-runtime-inspection"],
            ),
            "inspect_longest_sidekiq_job": ToolSpec(
                tool_id="inspect_longest_sidekiq_job",
                description="Record process, class, and runtime for the longest simulated job.",
                required_fact_ids=["gitlab-sidekiq-runtime-inspection"],
            ),
            "inspect_concurrency_rates": ToolSpec(
                tool_id="inspect_concurrency_rates",
                description="Compare simulated arrival and resume rates.",
                required_fact_ids=["gitlab-concurrency-backlog-response"],
            ),
            "set_sidekiq_concurrency_limit": ToolSpec(
                tool_id="set_sidekiq_concurrency_limit",
                description="Disable or restore a simulated worker concurrency limit.",
                arguments={"mode": "string"},
                mutating=True,
                required_fact_ids=["gitlab-concurrency-backlog-response"],
            ),
            "monitor_concurrency_queue": ToolSpec(
                tool_id="monitor_concurrency_queue",
                description="Read the simulated concurrency-limit queue drain signal.",
                required_fact_ids=["gitlab-concurrency-backlog-response"],
            ),
            "record_concurrency_root_cause": ToolSpec(
                tool_id="record_concurrency_root_cause",
                description="Record a simulated post-incident root-cause issue.",
                mutating=True,
                required_fact_ids=["gitlab-concurrency-backlog-response"],
            ),
        }
