---
layout: default
title: LLM-Enhanced Agents
---

# LLM-Enhanced Goal-Seeking Agents

The Azure infrastructure workload supports optional LLM integration for adaptive scenario execution via `LLMGoalSeekingAgent`.

## Overview

Standard `GoalSeekingAgent` executes static bash commands from scenario files. `LLMGoalSeekingAgent` extends this with three AI capabilities:

1. **Error Recovery** - When a command fails, the LLM suggests alternative commands
2. **Goal Evaluation** - LLM assesses whether scenario objectives were met
3. **Operations Commands** - LLM generates monitoring and verification commands

## Enabling LLM Integration

### Via CLI

```bash
haymaker deploy azure-infrastructure \
  --config scenario=linux-vm-web-server \
  --config enable_llm=true
```

### Via Config

```yaml
workload_name: azure-infrastructure
scenario: linux-vm-web-server
duration_hours: 4
enable_llm: true
```

## LLM Capabilities

### Error Recovery

When a deployment command fails, the agent asks the LLM:

```
Command: az vm create --name webserver --image UbuntuLTS
Error: The image 'UbuntuLTS' is deprecated
Scenario goal: Deploy a Linux web server

LLM suggests: az vm create --name webserver --image Ubuntu2204
```

The agent tries the suggested command. If the LLM responds `SKIP`, the failed step is skipped.

### Goal Evaluation

After deployment, the LLM evaluates recent logs against the scenario goal:

```
Scenario: linux-vm-web-server
Goal: Deploy a Linux web server with nginx
Recent logs: [deployment output...]

LLM evaluates: YES (goal achieved)
```

### Operations Command Generation

During the operations phase, the LLM generates monitoring commands appropriate for the scenario:

```
Scenario: linux-vm-web-server
Technology: Compute

LLM generates: az vm show --name webserver --query "powerState"
```

## Fallback Behavior

All LLM capabilities fall back gracefully:

| Capability | Without LLM |
|-----------|-------------|
| Error recovery | Skip failed command (no retry) |
| Goal evaluation | Assume success |
| Operations commands | Use static commands from scenario file |

The workload always completes even without an LLM configured.

## LLM Provider Setup

```bash
# Set provider (any agent-haymaker supported provider)
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Install AI dependencies
pip install haymaker-azure-workloads[ai]
```

See [agent-haymaker LLM docs](https://github.com/rysweet/agent-haymaker/blob/main/docs/llm-providers.md) for all provider options.

## Architecture

```
haymaker_azure_workloads/
├── agent.py          GoalSeekingAgent (standard)
├── llm_agent.py      LLMGoalSeekingAgent (LLM-enhanced)
├── workload.py       Agent selection based on enable_llm config
└── scenarios.py      Scenario loading and parsing
```

## Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `scenario` | string | required | Scenario name to execute |
| `duration_hours` | int | `8` | Operations phase duration |
| `region` | string | `eastus` | Azure region |
| `enable_llm` | bool | `false` | Enable LLM-enhanced agent |
