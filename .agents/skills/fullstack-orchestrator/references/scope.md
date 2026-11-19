# Functional scope and decision boundaries

## Supported product scope

Default scope is Web frontend/backend delivery and related data, algorithms and deployment preparation. Native mobile, desktop apps, mini-programs, browser extensions and hardware integrations require explicit task scope, applicable specialist resources and actual executor verification; Web evidence does not establish those capabilities. Do not install their toolchains merely to claim coverage.

## User choices and defaults

Software choices below are [this repository’s project policy](project-policy.md). When reused elsewhere, resolve that invoking project’s rules and permissions; these historical choices are not inherited defaults. Root/worktree ownership and runtime details follow [execution boundaries](execution-boundaries.md).

Codex chat is the only user-facing request, decision and result entry; fullstack-orchestrator is the sole coordination skill. The user may choose software per task or module. Main makes routine engineering decisions within authorization; only material unresolved business/visual choices, requested review gates and new permissions/costs/production actions require a user decision. Existing authorization persists. No selector website is required.

The current route, temporary availability and permitted dynamic candidates are defined only in [project policy](project-policy.md). Resolve that policy before selecting a frontend executor; do not infer a persistent default from historical runs. Codex owns backend, communication, database, algorithms, integration and acceptance where needed. Gemini is the LLM; Gemini Desktop and Antigravity are separate clients/transports. Model identity does not establish engineering or Stitch MCP access. Verify the selected client's actual tool connection, scope, grants and export capability. Work/Task labels require actual UI and capability verification. User-exclusive choices override AUTO. See [routing](routing.md).

Google AI Studio Build is an optional task-selected cloud frontend candidate/preview route, with account/Build/export capability NOT_TESTED until verified. It is not part of AUTO or an implicit fallback. See [cloud handoff boundaries](design-integration.md#google-ai-studio-build-optional); local shared/ grants do not transfer to the cloud.

## Full and partial invocation

This skill supports software-engineering task decisions for full-stack 0-to-1 delivery, incremental changes, diagnosis, review, upgrade, recovery and maintenance. Read [task decisions](task-decision.md) for seven execution modes, affected phases, executor selection, write scope and completion evidence. Select only affected phases under [scoped development](scoped-development.md); the functions below are conditional on actual impact, not a mandatory full pipeline. Preserve the existing product, contracts and stack; default to minimal compatible changes. Public GitHub reference discovery is enabled by default when it can materially inform an engineering decision, subject to bounded search, provenance and license checks. It does not authorize public uploads, installation or project replacement.

## Required workflow functions

1. Inspect the named project rules, relevant code, dirty state, stack, existing contracts and commands; preserve the real project. With no named product task, finish workflow preparation rather than invent features.
2. Record goal, non-goals, user flows, prerequisites and measurable acceptance. Route a narrow task directly; delegate when scope/dependencies justify it. Work on independent authorized items while others are blocked.
3. Establish minimal business, data, permission and API/event constraints before dependent frontend work. Existing schema/generators remain authoritative. Frontend can precede detailed backend implementation; independent backend preparation can proceed earlier. For cross-module API/event or database changes, freeze the relevant accepted revision and owner before dependent parallel work; use [engineering contracts](engineering-contracts.md). For selected external clients, task-required connection and grant evidence must match the current binding before READY; use [connection capabilities](connection-capabilities.md).
4. Obtain design candidates and actual usable exports. Cover affected navigation/actions and loading/empty/error/permission/submission states, responsive/accessibility behavior as applicable. Sample data and generated controls do not define business requirements.
5. Implement actual frontend and backend files. Mark Mock data, boundaries and switch points; real integration cannot be proved by Mock, screenshots, health checks or builds alone.
6. Collect, review and integrate source-bound artifacts; verify the final candidate, preserve task ownership and user changes, and report remaining limitations in Codex.
7. Retain minimal checkpoints and failure evidence; reconcile active/unknown attempts across software before any replay. See [handoff](handoff.md).

## Conditional engineering scope

| Domain | Include when relevant | Boundary |
|---|---|---|
| Design/frontend | real flows, forms, state, requests, responsive and accessibility behavior | no decorative filler or invented product scope |
| Backend | business logic, validation, authentication, authorization and object ownership | UI visibility is not server enforcement |
| Communication | request/response/errors, uploads, streaming/realtime/background jobs as required | no universal mandate for WebSockets or queues |
| Database | models, constraints, indexes, transactions, migrations and integrity | no unapproved destructive migration or production mutation |
| Algorithms/models | problem, baseline, protocol, dataset identity, metrics and limitations | label synthetic/provisional data, auth blocks and human review; no invented results |
| Deployment preparation | reproducible local startup, applicable config and checks | production action is separately authorized |
| Nonfunctional requirements | affected performance/resource budgets, compatibility, privacy, diagnostics and recovery | agree measurable targets for the actual product; do not add telemetry services or collect private data by default |
| Web/GitHub | bounded public upstream comparison for architecture, UI, communication, algorithms, tests or reusable skills when useful | follow scoped-development.md; no private source upload, automatic execution, installation or project replacement |

Do not add databases, algorithms, paid models or infrastructure merely to demonstrate full-stack coverage. A high-risk data/migration task requires its risk-specific checks and action authorization; ordinary edits need proportional checks.

## Skills and workers

For missing expertise or tools use [skill-discovery.md](skill-discovery.md): find-skills discovery, source/permission review, necessary project-level introduction, loading verification and rollback. Search proactively without repeatedly asking for already-authorized read-only discovery; do not install unrelated catalogs or overwrite the unique entry. Existing skills are sufficient unless an actual task reveals a gap.

Reuse actual installed specialist skills, selected by the project's stack. Native skill support in another app must be verified; otherwise deliver minimal relevant rules/resources and label this as task instructions, not native skill loading. Main's local tools/permissions do not automatically transfer to external software. Inspect referenced scripts at their actual owning toolkit; do not copy entire toolchains to satisfy a broken path.

Native subagents are authorized as needed. Main owns cross-software dispatch. Use configurable shared development capacity across participating projects on the same host/user (three or more tasks supported; see local-coordination.md), including Main when developing; read-only review can be scoped separately without violating write isolation. Acquire resources using [local coordination](local-coordination.md). One controller at a time operates the shared GUI. An existing app task belongs to its established owner; do not inspect unrelated private content, interrupt it, or claim its outputs. Record capabilities/grants rather than assuming skill prose enforces a sandbox.

## Non-goals and protected boundaries

No workflow website, dashboard, demo product, queue/database/daemon or autonomous background service. Do not restart historical demos or choose Campus QA changes without a real product request. Do not move installed software, duplicate every specialist, replace accounts/models/effort/proxies/routes, or refresh unrelated chat configurations.

The authorized minimal single-host coordinator is an exception only for shared resource metadata, not a global project-data store. It uses short file-lock transactions and persistent active grants, with explicit release after reconciliation. Distributed scheduling, automatic preemption, automatic production release and complex cost optimization are outside scope. All participants must use the same coordinator directory; no enforcement over other users or uncooperative tools is claimed.

No silent legal-term acceptance, paid upgrade, access expansion, production release or irreversible data operation. Prepare concrete reviewable work before seeking action-specific authorization. Do not write personal persistent memory. Local task checkpoints are not personal memory.

## Completion boundary

This skill supplies decision and coordination rules, not missing app integrations. App install/open/callability/file execution/recovery are separate facts. A bounded static/scenario check is not a real engineering or GUI acceptance test. Main may only promise waiting or continuation supported by actual tools, never unattended progress after execution stops. Acceptance and production authorization remain distinct. See [verification](verification.md).

## Location boundary

Consolidate this workflow's rules, task/handoff records and necessary sanitized evidence in the Codex project, while reusing a real product's native records where appropriate. Product source repositories, external application installations and authorized isolated workspaces keep their own locations. Do not move other projects or duplicate all source/skills merely to satisfy co-location. Record external workspace/artifact paths and identities explicitly; sharing the record folder does not grant software file access.
