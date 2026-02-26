"""Haymaker Azure Workloads - Azure infrastructure scenario execution.

This workload package provides goal-seeking agents that execute
Azure infrastructure scenarios, generating realistic telemetry.

Scenarios include:
    - Compute (VMs, App Service, Functions, Scale Sets)
    - Databases (MySQL, PostgreSQL, Cosmos DB)
    - Networking (VNets, Load Balancers, Application Gateway)
    - Security (Key Vault, Managed Identity)
    - AI/ML (Cognitive Services, OpenAI, ML Workspace)
    - And more...
"""

from .workload import AzureInfrastructureWorkload
from .llm_agent import LLMGoalSeekingAgent

__version__ = "0.1.0"

__all__ = [
    "AzureInfrastructureWorkload",
    "LLMGoalSeekingAgent",
    "__version__",
]
