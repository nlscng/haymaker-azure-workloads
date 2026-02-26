---
layout: default
title: Configuration
---

# Configuration

This page documents all configuration options for Haymaker Azure Workloads, including deployment settings, environment variables, and the workload manifest format.

## Deployment Configuration

Configuration is passed via the `--config` flag when deploying, or through a YAML configuration file.

### Options

| Option | Type | Default | Required | Description |
|--------|------|---------|----------|-------------|
| `scenario` | string | -- | Yes | Name of the scenario to execute (e.g., `linux-vm-web-server`) |
| `duration_hours` | integer | `8` | No | Duration of the operations phase in hours |
| `region` | string | `eastus` | No | Azure region for resource deployment |
| `enable_llm` | boolean | `false` | No | Enable LLM-powered adaptive agent behavior |

### Via CLI Flags

```bash
haymaker deploy azure-infrastructure \
  --config scenario=linux-vm-web-server \
  --config duration_hours=4 \
  --config region=westus2 \
  --config enable_llm=true
```

### Via YAML File

```yaml
workload_name: azure-infrastructure
scenario: linux-vm-web-server
duration_hours: 4
region: westus2
enable_llm: true
```

## Environment Variables

### Azure Credentials

The workload uses Azure CLI for all resource management. You must be authenticated before deploying.

```bash
# Interactive login
az login

# Service principal login (CI/CD)
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Set the target subscription
az account set --subscription $AZURE_SUBSCRIPTION_ID
```

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_SUBSCRIPTION_ID` | Yes | Target Azure subscription |
| `AZURE_CLIENT_ID` | For SP auth | Service principal application ID |
| `AZURE_CLIENT_SECRET` | For SP auth | Service principal secret |
| `AZURE_TENANT_ID` | For SP auth | Azure AD tenant ID |

### LLM Provider

When `enable_llm=true`, the workload requires LLM provider credentials. The agent uses the `agent-haymaker` LLM client, which supports multiple providers.

```bash
# Azure OpenAI
export LLM_PROVIDER=azure_openai
export AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-key-here
export AZURE_OPENAI_DEPLOYMENT=gpt-4

# Anthropic
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

| Variable | Required When | Description |
|----------|---------------|-------------|
| `LLM_PROVIDER` | `enable_llm=true` | LLM provider name (`azure_openai`, `anthropic`, `openai`) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | Azure OpenAI resource endpoint URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI | Model deployment name |
| `ANTHROPIC_API_KEY` | Anthropic | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI | OpenAI API key |

Install the AI extras to enable LLM support:

```bash
pip install "haymaker-azure-workloads[ai]"
```

See the [agent-haymaker LLM docs](https://github.com/rysweet/agent-haymaker/blob/main/docs/llm-providers.md) for full provider configuration details.

## Workload Manifest (workload.yaml)

The `workload.yaml` file in the repository root defines the workload metadata for the Agent Haymaker platform. This file is read by the `haymaker workload install` command.

```yaml
name: azure-infrastructure
version: "0.1.0"
type: runtime
description: "Azure infrastructure workloads with goal-seeking agents"

# Python package info
package:
  name: haymaker-azure-workloads
  entrypoint: haymaker_azure_workloads:AzureInfrastructureWorkload

# Target requirements
targets:
  - type: azure_subscription
    required_roles:
      - Contributor
      - User Access Administrator
    description: "Azure subscription for deploying infrastructure scenarios"

# Configuration schema
config_schema:
  scenario:
    type: string
    required: true
    description: "Name of the scenario to execute"
  duration_hours:
    type: integer
    default: 8
    description: "Duration of operations phase in hours"
  region:
    type: string
    default: "eastus"
    description: "Azure region for deployment"
  enable_llm:
    type: boolean
    default: false
    description: "Enable LLM-powered adaptive agent behavior"

# Available scenarios (populated from scenarios/ directory)
scenarios:
  compute:
    - linux-vm-web-server
    - windows-vm-iis
    - app-service-python
    - azure-functions-http
    - vm-scale-set
  databases:
    - mysql-wordpress
    - postgresql-django
    - cosmos-db-api
  networking:
    - virtual-network
    - load-balancer
    - application-gateway
  security:
    - key-vault-secrets
    - managed-identity
  ai-ml:
    - cognitive-services
    - azure-openai
    - ml-workspace
```

### Manifest Fields

| Field | Description |
|-------|-------------|
| `name` | Workload identifier used in `haymaker deploy <name>` |
| `version` | Semantic version of the workload package |
| `type` | Must be `runtime` for workloads that execute infrastructure |
| `description` | Human-readable workload description |
| `package.name` | PyPI package name |
| `package.entrypoint` | Python import path to the `WorkloadBase` subclass |
| `targets` | List of target environments with required Azure roles |
| `config_schema` | Schema for workload configuration options |
| `scenarios` | Registry of available scenarios organized by category |

## Azure Requirements

The target Azure subscription must have the following:

- **Contributor** role -- Required for creating and managing resources
- **User Access Administrator** role -- Required for managed identity and RBAC scenarios
- **Azure CLI** installed and authenticated on the machine running the workload
- Sufficient quota in the target region for the resources in the chosen scenario
