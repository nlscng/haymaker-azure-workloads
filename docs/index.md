---
layout: default
title: Home
---

# Haymaker Azure Workloads

Azure infrastructure workloads for the [Agent Haymaker](https://github.com/rysweet/agent-haymaker) platform. This package provides goal-seeking agents that deploy, operate, and clean up Azure infrastructure scenarios -- generating realistic telemetry for security and operations testing.

## How It Works

Each workload scenario follows a three-phase lifecycle:

1. **Deploy** -- Provision Azure resources (VMs, databases, networks, etc.) using Azure CLI commands
2. **Operate** -- Run the infrastructure for a configurable duration, generating telemetry and monitoring data
3. **Clean up** -- Remove all resources using tag-based tracking to ensure nothing is left behind

An optional LLM-enhanced agent mode adds adaptive error recovery, goal evaluation, and dynamic operations command generation.

## Quick Start

```bash
# Install the workload via haymaker CLI
haymaker workload install https://github.com/rysweet/haymaker-azure-workloads

# Or install via pip
pip install haymaker-azure-workloads

# Deploy a scenario
haymaker deploy azure-infrastructure --config scenario=linux-vm-web-server

# With custom duration and region
haymaker deploy azure-infrastructure \
  --config scenario=linux-vm-web-server \
  --config duration_hours=4 \
  --config region=westus2

# Monitor a running deployment
haymaker status <deployment-id>
haymaker logs <deployment-id> --follow

# Clean up resources
haymaker cleanup <deployment-id>
```

## Available Scenario Categories

### Compute
- `linux-vm-web-server` -- Ubuntu VM with Nginx
- `windows-vm-iis` -- Windows Server with IIS
- `app-service-python` -- Python web app on App Service
- `azure-functions-http` -- HTTP-triggered Azure Functions
- `vm-scale-set` -- Virtual Machine Scale Set

### Databases
- `mysql-wordpress` -- MySQL with WordPress
- `postgresql-django` -- PostgreSQL with Django app
- `cosmos-db-api` -- Cosmos DB with REST API

### Networking
- `virtual-network` -- VNet with subnets and NSGs
- `load-balancer` -- Load Balancer with backend pool
- `application-gateway` -- Application Gateway with WAF

### Security
- `key-vault-secrets` -- Key Vault secret management
- `managed-identity` -- Managed Identity with RBAC

### AI/ML
- `cognitive-services` -- Cognitive Services APIs
- `azure-openai` -- Azure OpenAI deployment
- `ml-workspace` -- Machine Learning workspace

## Documentation

- [LLM-Enhanced Agents](llm-enhanced-agents) -- Adaptive error recovery, goal evaluation, and operations command generation
- [Scenarios](scenarios) -- How scenarios work, three-phase execution, and creating custom scenarios
- [Configuration](configuration) -- All workload options, environment variables, and workload manifest format

## Requirements

- Azure subscription with Contributor role
- Azure CLI installed and authenticated
- [Agent Haymaker](https://github.com/rysweet/agent-haymaker) platform installed

## Development

```bash
git clone https://github.com/rysweet/haymaker-azure-workloads
cd haymaker-azure-workloads
pip install -e ".[dev]"
pytest
```

## Links

- [Agent Haymaker Platform](https://github.com/rysweet/agent-haymaker)
- [Source Code](https://github.com/rysweet/haymaker-azure-workloads)
- [PyPI Package](https://pypi.org/project/haymaker-azure-workloads/)
