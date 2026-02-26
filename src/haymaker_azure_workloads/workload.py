"""Azure Infrastructure Workload implementation.

Executes Azure infrastructure scenarios using goal-seeking agents
powered by Claude. Each scenario deploys Azure resources, operates
them for a period, then cleans up.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Any

from agent_haymaker import (
    WorkloadBase,
    DeploymentState,
    DeploymentConfig,
)
from agent_haymaker.workloads.models import CleanupReport, DeploymentStatus

from .scenarios import ScenarioLoader, Scenario
from .agent import GoalSeekingAgent


class AzureInfrastructureWorkload(WorkloadBase):
    """Workload for executing Azure infrastructure scenarios.

    This workload:
    1. Loads scenario definitions (prompts with Azure CLI commands)
    2. Creates a service principal for the deployment
    3. Runs a goal-seeking agent to execute the scenario
    4. Monitors execution and collects telemetry
    5. Cleans up Azure resources using tags
    """

    name = "azure-infrastructure"

    def __init__(self, platform: Any = None) -> None:
        super().__init__(platform)
        self._scenario_loader = ScenarioLoader()
        self._deployments: dict[str, DeploymentState] = {}
        self._agents: dict[str, GoalSeekingAgent] = {}

    async def deploy(self, config: DeploymentConfig) -> str:
        """Deploy an Azure infrastructure scenario.

        Args:
            config: Must include workload_config with:
                - scenario: Name of scenario to run (e.g., "linux-vm-web-server")
                - duration_hours: How long to run operations phase (default: 8)

        Returns:
            deployment_id for tracking
        """
        # Extract scenario name from config
        scenario_name = config.workload_config.get("scenario")
        if not scenario_name:
            raise ValueError("Config must include 'scenario' name")

        duration_hours = config.duration_hours or 8

        # Load scenario definition
        scenario = self._scenario_loader.load(scenario_name)
        if not scenario:
            available = self._scenario_loader.list_scenarios()
            raise ValueError(
                f"Scenario '{scenario_name}' not found. "
                f"Available: {', '.join(available)}"
            )

        # Choose agent class based on LLM availability
        agent_class = GoalSeekingAgent
        llm_client = None
        if config.workload_config.get("enable_llm", False):
            try:
                from agent_haymaker.llm import LLMConfig, create_llm_client
                from .llm_agent import LLMGoalSeekingAgent

                llm_config = LLMConfig.from_env()
                llm_client = create_llm_client(llm_config)
                agent_class = LLMGoalSeekingAgent
                self.log(f"LLM-enhanced agent enabled (provider: {llm_config.provider})")
            except Exception as e:
                self.log(f"LLM unavailable, using standard agent: {e}", level="WARNING")

        # Generate deployment ID
        deployment_id = f"azure-{uuid.uuid4().hex[:8]}"

        # Create deployment state
        state = DeploymentState(
            deployment_id=deployment_id,
            workload_name=self.name,
            status=DeploymentStatus.PENDING,
            phase="initializing",
            started_at=datetime.utcnow(),
            config={
                "scenario": scenario_name,
                "duration_hours": duration_hours,
                **config.workload_config,
            },
            metadata={
                "scenario_description": scenario.description,
                "technology_area": scenario.technology_area,
                "llm_enabled": llm_client is not None,
            },
        )
        self._deployments[deployment_id] = state

        # Create and start the goal-seeking agent
        agent_kwargs = dict(
            deployment_id=deployment_id,
            scenario=scenario,
            duration_hours=duration_hours,
            on_status_change=lambda phase, status: self._update_status(
                deployment_id, phase, status
            ),
        )
        if llm_client is not None:
            agent_kwargs["llm_client"] = llm_client
        agent = agent_class(**agent_kwargs)
        self._agents[deployment_id] = agent

        # Start execution (non-blocking)
        await agent.start()

        # Update state
        state.status = DeploymentStatus.RUNNING
        state.phase = "deploying"
        await self.save_state(state)

        return deployment_id

    async def get_status(self, deployment_id: str) -> DeploymentState:
        """Get current deployment state."""
        state = self._deployments.get(deployment_id)
        if not state:
            # Try loading from persistent storage
            state = await self.load_state(deployment_id)
            if state:
                self._deployments[deployment_id] = state

        if not state:
            from agent_haymaker.workloads.base import DeploymentNotFoundError
            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")

        return state

    async def stop(self, deployment_id: str) -> bool:
        """Stop a running deployment."""
        state = await self.get_status(deployment_id)
        agent = self._agents.get(deployment_id)

        if agent:
            await agent.stop()

        state.status = DeploymentStatus.STOPPED
        state.phase = "stopped"
        state.stopped_at = datetime.utcnow()
        await self.save_state(state)

        return True

    async def cleanup(self, deployment_id: str) -> CleanupReport:
        """Clean up all Azure resources for a deployment.

        Uses tag-based cleanup to find and delete all resources
        created by this deployment.
        """
        state = await self.get_status(deployment_id)
        agent = self._agents.get(deployment_id)

        report = CleanupReport(deployment_id=deployment_id)

        try:
            # Stop agent if running
            if agent and state.status == DeploymentStatus.RUNNING:
                await agent.stop()

            # Run cleanup phase
            state.status = DeploymentStatus.CLEANING_UP
            state.phase = "cleanup"
            await self.save_state(state)

            if agent:
                cleanup_result = await agent.cleanup()
                report.resources_deleted = cleanup_result.get("resources_deleted", 0)
                report.details = cleanup_result.get("details", [])

            # Mark completed
            state.status = DeploymentStatus.COMPLETED
            state.phase = "cleaned_up"
            state.completed_at = datetime.utcnow()
            await self.save_state(state)

        except Exception as e:
            report.errors.append(str(e))
            state.status = DeploymentStatus.FAILED
            state.error = str(e)
            await self.save_state(state)

        return report

    async def get_logs(
        self, deployment_id: str, follow: bool = False, lines: int = 100
    ) -> AsyncIterator[str]:
        """Stream logs for a deployment."""
        state = await self.get_status(deployment_id)
        agent = self._agents.get(deployment_id)

        if agent:
            async for line in agent.get_logs(follow=follow, lines=lines):
                yield line
        else:
            # Try loading from log file
            log_file = Path(f".haymaker/logs/{deployment_id}/agent.log")
            if log_file.exists():
                with open(log_file) as f:
                    log_lines = f.readlines()
                    for line in log_lines[-lines:]:
                        yield line

    async def validate_config(self, config: DeploymentConfig) -> list[str]:
        """Validate deployment configuration."""
        errors = await super().validate_config(config)

        scenario_name = config.workload_config.get("scenario")
        if not scenario_name:
            errors.append("workload_config must include 'scenario' name")
        else:
            # Check scenario exists
            scenario = self._scenario_loader.load(scenario_name)
            if not scenario:
                available = self._scenario_loader.list_scenarios()
                errors.append(
                    f"Scenario '{scenario_name}' not found. "
                    f"Available: {', '.join(available[:5])}..."
                )

        # Validate enable_llm type if provided
        enable_llm = config.workload_config.get("enable_llm")
        if enable_llm is not None and not isinstance(enable_llm, bool):
            errors.append("'enable_llm' must be a boolean value")

        return errors

    async def list_deployments(self) -> list[DeploymentState]:
        """List all Azure infrastructure deployments."""
        # Combine in-memory and persisted states
        states = list(self._deployments.values())

        # Also load from persistent storage if available
        if self._platform:
            persisted = await self._platform.list_deployments(self.name)
            # Merge, preferring in-memory state
            existing_ids = {s.deployment_id for s in states}
            for p in persisted:
                if p.deployment_id not in existing_ids:
                    states.append(p)

        return states

    def _update_status(self, deployment_id: str, phase: str, status: str) -> None:
        """Callback for agent status updates."""
        if deployment_id in self._deployments:
            state = self._deployments[deployment_id]
            state.phase = phase
            if status:
                state.status = DeploymentStatus(status)
