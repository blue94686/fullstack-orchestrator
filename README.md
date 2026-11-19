# Fullstack Orchestrator

Codex project-local software engineering workflow Skill. Current source revision: `1.4.0-project.40`.

The Skill routes software work by task scope, selecting only the necessary design, frontend, backend, integration, review, recovery, and verification stages. It supports new projects and incremental work while preserving project boundaries, existing user changes, tool permissions, and evidence-based completion.

## Install in a Codex project

Download and extract `fullstack-orchestrator-1.4.0-project.40.zip`, then copy `.agents/skills/fullstack-orchestrator/` into the target project's `.agents/skills/` directory, then invoke `$fullstack-orchestrator`. Read the Skill's project-scope and operations references before using external tools.

## Scope and verification

The versioned ZIP contains the Skill tree only. Its external integrity manifest records the SHA256 of the archive and every included source file. It does not include this authoring project's `AGENTS.md`, `WORKFLOW.md`, `shared/` exchange records, task evidence, local capacity configuration, or historical packages. A Skill package check proves file integrity, not that Stitch, Gemini, Antigravity, AI Studio, or any product workflow is connected or has passed end-to-end acceptance. Tool access, project rules, and execution evidence must be checked in each invoking project.
