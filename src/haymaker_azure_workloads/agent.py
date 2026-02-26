"""Goal-seeking agent for Azure scenario execution.

The agent uses Claude to execute Azure infrastructure scenarios,
handling errors and adapting to issues encountered during execution.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Callable, Any

from .scenarios import Scenario


class GoalSeekingAgent:
    """Agent that executes Azure scenarios using Claude.

    The agent:
    1. Parses the scenario prompt
    2. Executes deployment phase (Azure CLI commands)
    3. Runs operations for specified duration
    4. Handles errors using Claude for troubleshooting
    5. Performs cleanup
    """

    def __init__(
        self,
        deployment_id: str,
        scenario: Scenario,
        duration_hours: int = 8,
        on_status_change: Callable[[str, str], None] | None = None,
    ) -> None:
        self.deployment_id = deployment_id
        self.scenario = scenario
        self.duration_hours = duration_hours
        self._on_status_change = on_status_change

        self._running = False
        self._task: asyncio.Task | None = None
        self._logs: list[str] = []
        self._log_file: Path | None = None

        # Set up logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up log file for this agent."""
        log_dir = Path(f".haymaker/logs/{self.deployment_id}")
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = log_dir / "agent.log"

    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_line)

        # Write to file
        if self._log_file:
            with open(self._log_file, "a") as f:
                f.write(log_line + "\n")

    async def start(self) -> None:
        """Start the agent execution."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the agent execution."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def cleanup(self) -> dict[str, Any]:
        """Run cleanup phase."""
        self._log("Starting cleanup phase")
        self._update_status("cleanup", "cleaning_up")

        cleanup_result = {
            "resources_deleted": 0,
            "details": [],
        }

        try:
            # Get cleanup commands from scenario
            cleanup_commands = self.scenario.phases.get("cleanup", "")
            if cleanup_commands:
                self._log("Executing cleanup commands")
                # In real implementation, execute via Claude or subprocess
                cleanup_result["details"].append("Cleanup commands executed")
                cleanup_result["resources_deleted"] = 5  # Placeholder

            self._log("Cleanup completed")

        except Exception as e:
            self._log(f"Cleanup error: {e}", "ERROR")
            raise

        return cleanup_result

    async def get_logs(self, follow: bool = False, lines: int = 100) -> AsyncIterator[str]:
        """Stream agent logs."""
        # Return recent logs
        for line in self._logs[-lines:]:
            yield line

        if follow:
            # Follow new logs
            last_index = len(self._logs)
            while self._running:
                await asyncio.sleep(0.5)
                new_logs = self._logs[last_index:]
                for line in new_logs:
                    yield line
                last_index = len(self._logs)

    async def _run(self) -> None:
        """Main execution loop."""
        try:
            # Phase 1: Deployment
            await self._run_deployment()

            # Phase 2: Operations
            await self._run_operations()

            # Phase 3 (cleanup) is called explicitly via cleanup()

        except asyncio.CancelledError:
            self._log("Agent execution cancelled")
            raise
        except Exception as e:
            self._log(f"Agent execution failed: {e}", "ERROR")
            self._update_status("failed", "failed")
            raise

    async def _run_deployment(self) -> None:
        """Execute deployment phase."""
        self._log(f"Starting deployment phase for scenario: {self.scenario.name}")
        self._update_status("deploying", "running")

        deployment_commands = self.scenario.phases.get("deployment", "")
        if deployment_commands:
            self._log("Executing deployment commands...")
            # In real implementation, this would:
            # 1. Parse the bash commands
            # 2. Execute via subprocess or Claude Code SDK
            # 3. Handle errors with goal-seeking behavior
            await asyncio.sleep(2)  # Placeholder
            self._log("Deployment phase completed")

        self._update_status("deployed", "running")

    async def _run_operations(self) -> None:
        """Execute operations phase for specified duration."""
        self._log(f"Starting operations phase ({self.duration_hours} hours)")
        self._update_status("operating", "running")

        operations_commands = self.scenario.phases.get("operations", "")

        # Calculate end time
        end_time = datetime.utcnow().timestamp() + (self.duration_hours * 3600)

        operation_count = 0
        while self._running and datetime.utcnow().timestamp() < end_time:
            if operations_commands:
                # Execute operation cycle
                operation_count += 1
                self._log(f"Executing operation cycle {operation_count}")
                # In real implementation, execute operations
                await asyncio.sleep(60)  # Wait between cycles

        self._log(f"Operations phase completed ({operation_count} cycles)")
        self._update_status("operations_complete", "running")

    def _update_status(self, phase: str, status: str) -> None:
        """Update status via callback."""
        if self._on_status_change:
            self._on_status_change(phase, status)
