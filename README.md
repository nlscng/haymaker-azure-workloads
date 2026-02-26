# Haymaker Azure Workloads

Azure infrastructure workloads for Agent Haymaker platform.

## Overview

This package provides workloads that execute Azure infrastructure scenarios using goal-seeking agents. Each scenario:

1. **Deploys** Azure resources (VMs, databases, networks, etc.)
2. **Operates** for a specified duration, generating telemetry
3. **Cleans up** all resources using tag-based tracking

## Installation

```bash
# Install via haymaker CLI
haymaker workload install https://github.com/rysweet/haymaker-azure-workloads

# Or via pip
pip install haymaker-azure-workloads
```

## Usage

```bash
# Deploy a scenario
haymaker deploy azure-infrastructure --config scenario=linux-vm-web-server

# With custom duration
haymaker deploy azure-infrastructure \
  --config scenario=linux-vm-web-server \
  --config duration_hours=4 \
  --config region=westus2

# Monitor
haymaker status <deployment-id>
haymaker logs <deployment-id> --follow

# Cleanup
haymaker cleanup <deployment-id>
```

## Available Scenarios

### Compute
- `linux-vm-web-server` - Ubuntu VM with Nginx
- `windows-vm-iis` - Windows Server with IIS
- `app-service-python` - Python web app on App Service
- `azure-functions-http` - HTTP-triggered Azure Functions
- `vm-scale-set` - Virtual Machine Scale Set

### Databases
- `mysql-wordpress` - MySQL with WordPress
- `postgresql-django` - PostgreSQL with Django app
- `cosmos-db-api` - Cosmos DB with REST API

### Networking
- `virtual-network` - VNet with subnets and NSGs
- `load-balancer` - Load Balancer with backend pool
- `application-gateway` - Application Gateway with WAF

### Security
- `key-vault-secrets` - Key Vault secret management
- `managed-identity` - Managed Identity with RBAC

### AI/ML
- `cognitive-services` - Cognitive Services APIs
- `azure-openai` - Azure OpenAI deployment
- `ml-workspace` - Machine Learning workspace

## Creating Custom Scenarios

Add a new scenario by creating a markdown file in `scenarios/`:

```markdown
# Scenario: My Custom Scenario

## Technology Area
Compute

## Scenario Description
Deploy a custom infrastructure setup.

## Azure Services Used
- Azure Virtual Machines
- Azure Storage

## Phase 1: Deployment and Validation

```bash
# Create resource group
az group create --name mygroup --location eastus --tags AzureHayMaker-managed=true

# Deploy resources
az vm create ...
```

## Phase 2: Operations and Management

```bash
# Perform operations
az vm run-command invoke ...
```

## Phase 3: Cleanup

```bash
# Delete all resources
az group delete --name mygroup --yes --no-wait
```
```

## LLM-Enhanced Agents

The workload supports optional LLM integration for adaptive scenario execution. When enabled, the `LLMGoalSeekingAgent` extends the standard agent with:

- **Adaptive error recovery** - When a command fails, the LLM suggests alternative commands to achieve the same goal
- **Goal evaluation** - After execution, the LLM assesses whether the scenario objectives were met
- **Operations command generation** - The LLM generates monitoring and verification commands appropriate for the deployed scenario

### Enabling LLM Integration

```bash
haymaker deploy azure-infrastructure \
  --config scenario=linux-vm-web-server \
  --config enable_llm=true
```

### Environment Variables

LLM integration requires the `agent-haymaker[llm]` optional dependency and appropriate environment variables for your LLM provider (e.g., `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`). See the [agent-haymaker LLM docs](https://github.com/rysweet/agent-haymaker) for provider configuration.

### Fallback Behavior

When LLM is unavailable (not installed, misconfigured, or API errors), the agent falls back to standard static command execution. No scenario functionality is lost -- LLM features are purely additive.

Install the AI extras to enable LLM support:

```bash
pip install "haymaker-azure-workloads[ai]"
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `scenario` | string | required | Scenario name to execute |
| `duration_hours` | int | 8 | Operations phase duration |
| `region` | string | eastus | Azure region |
| `enable_llm` | bool | false | Enable LLM-powered adaptive agent behavior |

## Requirements

- Azure subscription with Contributor role
- Azure CLI installed and authenticated
- [Agent Haymaker](https://github.com/rysweet/agent-haymaker) platform installed

## Development

```bash
# Clone
git clone https://github.com/rysweet/haymaker-azure-workloads
cd haymaker-azure-workloads

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- [LLM-Enhanced Agents Guide](docs/llm-enhanced-agents.md) - Error recovery, goal evaluation, operations commands, fallback behavior

## License

MIT
