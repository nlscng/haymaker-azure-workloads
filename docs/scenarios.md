---
layout: default
title: Scenarios
---

# Scenarios

Scenarios are the core unit of work in Haymaker Azure Workloads. Each scenario is a self-contained markdown file that describes an Azure infrastructure deployment, including the Azure CLI commands needed to provision, operate, and tear down resources.

## How Scenarios Work

A scenario is defined as a markdown file stored in the `scenarios/` directory within the package. The `ScenarioLoader` class parses these files and extracts structured data that the goal-seeking agent uses to execute the deployment.

### Scenario Data Model

When a scenario file is loaded, it is parsed into a `Scenario` dataclass with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Derived from the filename (e.g., `linux-vm-web-server`) |
| `description` | `str` | Extracted from the `## Scenario Description` section |
| `technology_area` | `str` | Extracted from `## Technology Area` (e.g., Compute, Databases) |
| `goal` | `str` | Extracted from `## Goal`, falls back to `description` |
| `prompt` | `str` | The full markdown content, used as the agent prompt |
| `phases` | `dict[str, str]` | Maps phase names to their bash command blocks |

### ScenarioLoader

The `ScenarioLoader` handles finding and parsing scenario files.

```python
from haymaker_azure_workloads.scenarios import ScenarioLoader

loader = ScenarioLoader()

# List all available scenarios
names = loader.list_scenarios()
# ['compute/linux-vm-web-server', 'databases/mysql-wordpress', ...]

# Load a specific scenario
scenario = loader.load("linux-vm-web-server")
print(scenario.technology_area)  # "Compute"
print(scenario.phases.keys())    # dict_keys(['deployment', 'operations', 'cleanup'])
```

The loader searches for scenarios in three ways:
1. **Exact match** -- `scenarios/{name}.md`
2. **Category prefix** -- `scenarios/{category}/{name}.md`
3. **Substring search** -- Any `.md` file under `scenarios/` whose stem contains the name

## Three-Phase Execution

Every scenario is structured around three phases that map to the deployment lifecycle.

### Phase 1: Deployment and Validation

The deployment phase provisions Azure resources. Commands in this phase typically create resource groups, deploy services, and validate that resources are accessible.

All resources must be tagged with `AzureHayMaker-managed=true` to enable tag-based cleanup.

```bash
# Create resource group with tracking tag
az group create --name mygroup --location eastus --tags AzureHayMaker-managed=true

# Deploy resources
az vm create --resource-group mygroup --name webserver --image Ubuntu2204 ...

# Validate deployment
az vm show --resource-group mygroup --name webserver --query "provisioningState"
```

### Phase 2: Operations and Management

The operations phase runs for the configured `duration_hours` (default: 8 hours). Commands in this phase perform monitoring, health checks, and operational tasks that generate telemetry.

When LLM mode is enabled, the agent can also generate additional monitoring commands dynamically based on the scenario context.

```bash
# Check VM status
az vm get-instance-view --resource-group mygroup --name webserver --query "instanceView.statuses[1]"

# Monitor metrics
az monitor metrics list --resource mygroup --metric "Percentage CPU"
```

### Phase 3: Cleanup

The cleanup phase removes all Azure resources created during deployment. Tag-based cleanup ensures all resources are found even if the deployment created additional resources not explicitly listed.

```bash
# Delete resource group (removes all contained resources)
az group delete --name mygroup --yes --no-wait
```

## Available Scenario Categories

Scenarios are organized into category directories.

### Compute
| Scenario | Description |
|----------|-------------|
| `linux-vm-web-server` | Ubuntu VM with Nginx web server |
| `windows-vm-iis` | Windows Server with IIS |
| `app-service-python` | Python web app on App Service |
| `azure-functions-http` | HTTP-triggered Azure Functions |
| `vm-scale-set` | Virtual Machine Scale Set with autoscaling |

### Databases
| Scenario | Description |
|----------|-------------|
| `mysql-wordpress` | MySQL Flexible Server with WordPress |
| `postgresql-django` | PostgreSQL with Django application |
| `cosmos-db-api` | Cosmos DB with REST API |

### Networking
| Scenario | Description |
|----------|-------------|
| `virtual-network` | VNet with subnets and NSGs |
| `load-balancer` | Load Balancer with backend pool |
| `application-gateway` | Application Gateway with WAF |

### Security
| Scenario | Description |
|----------|-------------|
| `key-vault-secrets` | Key Vault secret management |
| `managed-identity` | Managed Identity with RBAC |

### AI/ML
| Scenario | Description |
|----------|-------------|
| `cognitive-services` | Cognitive Services APIs |
| `azure-openai` | Azure OpenAI model deployment |
| `ml-workspace` | Machine Learning workspace |

## Creating Custom Scenarios

To add a new scenario, create a markdown file in the appropriate category directory under `scenarios/`. The file must follow this structure:

```markdown
# Scenario: My Custom Scenario

## Technology Area
Compute

## Scenario Description
Deploy a custom infrastructure setup with specific requirements.

## Goal
Successfully deploy and validate a custom compute environment.

## Azure Services Used
- Azure Virtual Machines
- Azure Storage

## Phase 1: Deployment and Validation

```bash
# Create resource group with required tag
az group create --name mygroup --location eastus --tags AzureHayMaker-managed=true

# Deploy resources
az vm create --resource-group mygroup --name myvm --image Ubuntu2204 \
  --size Standard_B2s --admin-username azureuser --generate-ssh-keys

# Validate
az vm show --resource-group mygroup --name myvm --query "provisioningState"
```

## Phase 2: Operations and Management

```bash
# Monitor VM
az vm get-instance-view --resource-group mygroup --name myvm \
  --query "instanceView.statuses[1].displayStatus"

# Check metrics
az monitor metrics list --resource mygroup --metric "Percentage CPU" --interval PT1H
```

## Phase 3: Cleanup

```bash
# Delete all resources
az group delete --name mygroup --yes --no-wait
```
```

### Key Requirements for Custom Scenarios

1. **Tag all resources** -- Include `--tags AzureHayMaker-managed=true` on resource group creation for reliable cleanup.
2. **Use phase headers** -- The parser looks for headers matching `Phase 1.*Deployment`, `Phase 2.*Operations`, and `Phase 3.*Cleanup`.
3. **Bash code blocks** -- All commands must be in fenced code blocks marked as `bash`.
4. **Include metadata sections** -- `Technology Area`, `Scenario Description`, and optionally `Goal` sections provide context to the agent.
5. **Place in category directory** -- Put the file under the appropriate `scenarios/{category}/` subdirectory (e.g., `scenarios/compute/my-scenario.md`).

### Custom Scenarios Directory

You can also point the `ScenarioLoader` at a custom directory:

```python
from pathlib import Path
from haymaker_azure_workloads.scenarios import ScenarioLoader

loader = ScenarioLoader(scenarios_dir=Path("/path/to/my/scenarios"))
scenario = loader.load("my-custom-scenario")
```
