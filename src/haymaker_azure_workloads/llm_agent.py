"""LLM-enhanced goal-seeking agent for adaptive Azure scenario execution.

When an LLM client is available, this agent can:
- Generate adaptive commands based on scenario goals and current state
- Recover from errors by asking the LLM for alternative approaches
- Evaluate whether scenario goals have been achieved

Falls back to static command execution when no LLM is configured.

Public API (the "studs"):
    LLMGoalSeekingAgent: Enhanced agent with LLM capabilities
"""

import asyncio
import logging
from pathlib import Path

from .agent import GoalSeekingAgent
from .scenarios import Scenario

logger = logging.getLogger(__name__)


class LLMGoalSeekingAgent(GoalSeekingAgent):
    """Goal-seeking agent enhanced with LLM capabilities.

    Extends GoalSeekingAgent with optional LLM integration for:
    - Adaptive command generation
    - Error recovery
    - Goal evaluation

    Falls back to parent class behavior when no LLM is available.
    """

    def __init__(
        self,
        deployment_id: str,
        scenario: Scenario,
        duration_hours: int = 8,
        on_status_change=None,
        llm_client=None,
    ):
        """Initialize LLM-enhanced agent.

        Args:
            deployment_id: Unique deployment identifier
            scenario: Scenario definition to execute
            duration_hours: How long to run operations phase
            on_status_change: Callback for status changes
            llm_client: Optional BaseLLMProvider from agent_haymaker.llm
        """
        super().__init__(
            deployment_id=deployment_id,
            scenario=scenario,
            duration_hours=duration_hours,
            on_status_change=on_status_change,
        )
        self._llm_client = llm_client

    @property
    def has_llm(self) -> bool:
        """Whether an LLM client is available."""
        return self._llm_client is not None

    async def _handle_command_error(
        self, command: str, error: str, phase: str
    ) -> str | None:
        """Ask LLM for error recovery suggestions.

        Args:
            command: The command that failed
            error: Error output
            phase: Current execution phase

        Returns:
            Alternative command to try, or None to skip
        """
        if not self._llm_client:
            return None

        try:
            from agent_haymaker.llm import LLMMessage

            prompt = (
                f"An Azure CLI command failed during the {phase} phase of "
                f"scenario '{self.scenario.name}'.\n\n"
                f"Command: {command}\n"
                f"Error: {error}\n\n"
                f"Scenario goal: {self.scenario.goal}\n\n"
                f"Suggest ONE alternative command that might achieve the same goal, "
                f"or respond with 'SKIP' if this step should be skipped.\n"
                f"Return ONLY the command (no explanation)."
            )

            response = await self._llm_client.create_message_async(
                messages=[LLMMessage(role="user", content=prompt)],
                system="You are an Azure infrastructure expert. Provide only CLI commands.",
                max_tokens=200,
                temperature=0.3,
            )

            suggestion = response.content.strip()
            if suggestion.upper() == "SKIP":
                logger.info(f"LLM suggests skipping failed command: {command}")
                return None

            logger.info(f"LLM suggests alternative: {suggestion}")
            return suggestion

        except Exception as e:
            logger.warning(f"LLM error recovery failed: {e}")
            return None

    async def _evaluate_goal(self) -> bool:
        """Ask LLM to evaluate whether the scenario goal has been achieved.

        Returns:
            True if goal appears achieved, False otherwise
        """
        if not self._llm_client:
            return True  # Assume success without LLM

        try:
            from agent_haymaker.llm import LLMMessage

            recent_logs = self._logs[-20:]
            log_text = "\n".join(recent_logs) if recent_logs else "(no logs)"

            prompt = (
                f"Scenario: {self.scenario.name}\n"
                f"Goal: {self.scenario.goal}\n\n"
                f"Recent execution logs:\n{log_text}\n\n"
                f"Based on the logs, has the scenario goal been achieved? "
                f"Respond with only 'YES' or 'NO'."
            )

            response = await self._llm_client.create_message_async(
                messages=[LLMMessage(role="user", content=prompt)],
                system="You evaluate Azure infrastructure deployment outcomes.",
                max_tokens=10,
                temperature=0.1,
            )

            return response.content.strip().upper().startswith("YES")

        except Exception as e:
            logger.warning(f"LLM goal evaluation failed: {e}")
            return True  # Assume success on evaluation failure

    async def _generate_operations_command(self) -> str | None:
        """Ask LLM to generate a monitoring/operations command.

        Returns:
            Command to execute, or None
        """
        if not self._llm_client:
            return None

        try:
            from agent_haymaker.llm import LLMMessage

            prompt = (
                f"Scenario: {self.scenario.name}\n"
                f"Goal: {self.scenario.goal}\n"
                f"Technology: {self.scenario.technology_area}\n\n"
                f"Generate ONE Azure CLI monitoring or verification command "
                f"appropriate for this deployed scenario.\n"
                f"Return ONLY the command (no explanation)."
            )

            response = await self._llm_client.create_message_async(
                messages=[LLMMessage(role="user", content=prompt)],
                system="You are an Azure operations expert. Return only CLI commands.",
                max_tokens=200,
                temperature=0.5,
            )

            return response.content.strip()

        except Exception as e:
            logger.warning(f"LLM command generation failed: {e}")
            return None


__all__ = ["LLMGoalSeekingAgent"]
