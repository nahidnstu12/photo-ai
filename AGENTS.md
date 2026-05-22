# AGENTS.md — photo-ai

Entry point for AI coding agents.

## Start here

1. [docs/00-plan.md](docs/00-plan.md) — locked decisions, phase order
2. [docs/agent-guidelines.md](docs/agent-guidelines.md) — how to work in this repo
3. [docs/phases/](docs/phases/) — implement **one phase at a time**

## Current work

**Phase 1:** [docs/phases/01-docker-foundation.md](docs/phases/01-docker-foundation.md)

## Rules

- `.cursor/rules/core.mdc` — always apply
- `.cursor/rules/docker.mdc` — compose & Dockerfiles
- `.cursor/rules/python-pipeline.mdc` — orchestrator Python code

## Do not

- Skip phases or implement ComfyUI before Phase 4
- Commit model weights or generated images
- Use denoise > 0.35 for catalog mode without explicit user request
- Add cloud API dependencies
