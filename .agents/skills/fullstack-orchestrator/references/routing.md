# Routing and compatibility

Rule ownership: task-decision.md owns scope/stage decisions; project-policy.md records only this repository’s choices; skill-discovery.md owns specialist loading/discovery; handoff.md owns task identity, incremental context and artifact index; closed-loop.md owns transition/closeout guards. Read the applicable owner rather than loading every reference; summaries here do not create additional gates.

Resolve the invoking project policy first. Current software defaults in this document describe [this repository](project-policy.md), not authorization for other projects. Apply [execution boundaries](execution-boundaries.md) for capability invalidation, competing coordinators and resource stops.

Discover current skill metadata in the session catalog and installed skill roots; resolve their real paths. Read the chosen SKILL.md before relying on it. Record missing paths, unsupported generators or incompatible stacks; do not claim a named historical version is installed without evidence.

For actual loading, delegation, composition and use evidence follow [calling existing Skills](skill-discovery.md#按需调用现有-skills). Candidate names below are recommendations, not automatic dispatch or installed-tool claims.

AI-SDLC v1.2 is a requested reuse candidate, not a guaranteed dependency. If it cannot be located, state this and use verified specialists. Existing `ai-fullstack-delivery` may help engineering governance. Existing `vibe-fullstack-router` may suggest phases, but its recommended downstream names must each be checked; do not load missing or React-only skills for Vue.

Before running a referenced helper, resolve it against the owning toolkit and verify that file exists. Some older governance skills reference `scripts/` relative to a separate Controller checkout, not their own skill folder or the user's current repository. Do not execute those commands from an arbitrary cwd or copy the entire legacy Controller into a project. A missing helper blocks only its dependent operation; use an available project-native command when equivalent and authorized.

| Actual task | Existing candidates, when present |
|---|---|
| Missing capability / discovery | find-skills; skill-installer only when reviewed installation is needed; skill-creator for a justified reusable local gap |
| Understand repo/scope | codebase-context-reader, product-requirement-planner |
| Backend/data | backend-api-builder, database-data-workflow |
| Auth/ownership | auth-permission-security |
| Frontend | frontend-feature-builder; frontend-design only for visual work |
| API/event consumers | api-contract-sync |
| Debugging | systematic-debugging |
| Quality | testing-release-gate, verification-before-completion |
| Containers/release | devops-deployment-docker |
| Isolation | using-git-worktrees or the platform's existing isolated workspace |
| Stitch design | connected and authorized Stitch MCP in Codex first when it supports the required operation; otherwise authorized Stitch Desktop or another applicable transport; honor an explicit per-task preference |

Do not install all candidates. If local capability is sufficient, proceed. For actual gaps use [skill-discovery.md](skill-discovery.md), including find-skills when available. The user authorizes proactive search and necessary reviewed project-level supplementation; this does not authorize replacing existing configuration or global installation. Never report a cached plugin as authenticated/callable.

Use the narrowest scope. Existing business rules and user authorization govern implementation. If UI, backend and schema are tightly dependent, Main freezes shared inputs first; then only independent tasks run concurrently. Main alone accepts proposed contract changes. Permissions, migrations and production changes warrant independent review when risk justifies it; routine small work does not need repeated agents.

Serialize concurrent writes within a shared mutable workspace by default. Parallel writes require separate worktrees or equivalent isolation, checked baselines, clear ownership and an integration path. Coordinate shared contracts, migrations, lockfiles and generators through Main even across separate worktrees. A dependent task starts only after its prerequisite meets the acceptance criteria needed by that dependency.

## Executor selection and blocked dependencies

Default HYBRID: for each delegated task identify its primary executor, required dependencies, scope and any permitted fallback before dispatch. Check only executors this task actually needs, at the point their availability matters; do not probe dormant providers or create a formal plan for a one-line edit. Distinguish app/transport from model: the installed Gemini Desktop Work mode is its own desktop route; an eventual Gemini model inside an Antigravity transport is not an additional independent worker. Resolve the long-term preference and current temporary availability from [project policy](project-policy.md). Do not probe a route still covered by an unchanged unavailability report; historic success or failure alone does not establish present capability.

If a required executor is unavailable, mark that task and its dependent tasks BLOCKED; continue genuinely independent authorized work. If the user explicitly requires all selected executors before any work, stop the whole requested workflow. An optional unavailable executor can be omitted. A fallback requires user authorization from the current request or prior session, and compatibility with needed capability, real grants, write scope, cost and acceptance; record the actual executor. An agent-authored plan cannot grant that authorization. Earlier authorization never overrides a later pause or exclusive-route restriction. A user-selected exclusive route remains binding; an explicitly authorized dynamic route may switch as described below. Never call an unavailable node successful.

Classify the result before retry or fallback: an unknown execution outcome needs read-only reconciliation first; access denial, authentication failure or out-of-scope writes are not reasons to switch around the boundary. A transient failure or quota limit permits retry or an authorized fallback only after side effects are resolved; don't retry blindly. Test failures return to the responsible task for diagnosis. Do not broaden the failure to unrelated tasks.

An executor busy with an unrelated task is BUSY, not evidence of quota exhaustion or a failed task. Do not inspect its private content, interrupt it or claim its results. Defer the new dispatch, continue independent work and use an authorized alternative only when the user's route permits it. When ownership of an existing task cannot be established, keep the outcome UNKNOWN; do not infer identity from a similar title.

## Cost-aware execution

Default limits: shared configured development capacity across participating projects on this host/user (including Main when developing; see local-coordination.md), normally at most two per project, one desktop GUI controller, and two repair rounds for one issue. Acquire/check/release actual grants using [local coordination](local-coordination.md); BUSY defers only dependent actions. The helper supports a finite eligible-order wait list, retried only by an active Main; it has no automatic dispatch, wakeup, preemption or timeout release. Read project instructions and the smallest relevant file set first; use task summaries, Git diff and bounded failure excerpts instead of whole repositories or logs. Send each worker only necessary context and acceptance. Prefer the project's deterministic tests to repeated model reviews; independently review high-risk work as needed. Reuse evidence only when its inputs, environment and affected scope still match; invalidate affected checks on relevant change. Poll asynchronous work sparingly using its real status or completion notification; inspect the GUI only when necessary to determine the next action. Do not lower or change the user's model/reasoning setting without their direction.

Record actual elapsed time and accessible token/cost data; otherwise mark UNKNOWN. When available without extra instrumentation, compare equivalent tasks using actual worker/tool calls, relevant file-read ranges, retries and the same quality checks. Do not turn proxies into estimated token or money savings. A smaller prompt, bounded delegation or cached evidence is a technique, not proof of savings. Re-evaluate an executor after a relevant app/tool/skill/OS version change, not after every unrelated code edit.

## Dynamic route selection

Record a compact per-task choice in chat or the existing checkpoint: `route=AUTO|ANTIGRAVITY_CLI|ANTIGRAVITY_DESKTOP|GEMINI_DESKTOP_WORK|AI_STUDIO_BUILD|CODEX`, ordered permitted fallbacks, and `analysis=LOCAL|WEB`. This is a workflow choice, not a requirement to build a selector UI. The user's latest explicit authorization supersedes older workflow defaults; preserve target-project rules that remain applicable and report actual conflicts.

AI_STUDIO_BUILD is an optional explicitly task-selected cloud frontend candidate/preview route; read [its handoff boundaries](design-integration.md#google-ai-studio-build-optional). Adding it to the available software does not change AUTO, create an automatic Gemini fallback, authorize cloud uploads of sensitive source, or establish runtime capability. Record it in resolved_routes only when selected or authorized as a fallback for that assignment. Use existing task records and reconciliation; do not create another dispatcher.

For this project AUTO follows project-policy.md: Gemini Desktop Work/Task is the temporary external route while Antigravity is unavailable; Codex may be selected as an authorized frontend candidate. CLI-first is the long-term preference, restored for future assignments only after the applicable policy and capability gates are satisfied. Record the task-specific reason and reuse the same conversation. This does not change exclusive routes.

Only probe the selected, currently authorized route; desktop routes use actual UI/tool observations, not CLI discovery. For a selected CLI, probe cheaply: discover executable and supported options, then make one bounded minimal real request in a scratch context when authorized and necessary. Record transport, configured model when observable, outcome and time; preserve configured model/effort and do not dump credentials or global configuration. No repeated probes while the same blocker is unchanged. Re-select only at a task boundary (including an authorized task-specific choice) or after confirmed failure and reconciliation, never mid-flight merely because another route looks faster. Keep failed attempt evidence and a new attempt ID for a fallback; acceptance and writable scope remain unchanged. Returning availability affects subsequent assignments, not active ones.

When WEB analysis is authorized, prefer an existing user-designated chat. Send only task-relevant, sanitized context; no credentials, private datasets or whole repositories. Record the conversation locator and returned recommendations. Web analysis is advisory: Main checks claims against actual source and tests; it does not grant filesystem execution or prove CLI/Desktop success. Opening an analysis chat does not authorize building a workflow website.

## Selected software and local availability

Gemini is the LLM, not an execution client. This project’s desktop frontend route uses **Gemini Desktop Task**; older requests also used Work. AI Studio Build and Antigravity remain distinct clients/routes even when they expose a Gemini model. Verify the actual UI label and capabilities; never force a mode switch based on naming or substitute standalone CLI/API or generic chat. Antigravity CLI and Desktop are transports of the same software; model identity is separate. Antigravity may use its already configured Gemini model to call Stitch tools through its MCP client only after verifying actual MCP connectivity and export permissions. When the applicable project rules permit the route and both Antigravity transports are known unavailable, go directly to independently authorized Gemini Work without repeated probes. CLI technical unavailability permits Desktop; authentication/policy/service suspension does not authorize using another transport to circumvent that restriction. Reconcile old attempts before every switch. If Gemini is unavailable, block dependent frontend work unless another route (such as AI Studio Build or Codex) was separately selected or permitted as a fallback for this task. Codex continues independent backend work.

Main may use native subagents and verified specialists; native tools and local skills are not automatically available to external agents. Use native Skill support where verified, otherwise pass minimal task rules and record the difference. Claude is currently absent; use only after explicit selection and verified access. Stitch direct access from Antigravity is optional and must be verified; otherwise Main collects and hands off its resources.

Cache availability only in the existing project record: executor/capability, nonsecret auth scope, observed time, evidence, reason and recheck trigger. Relevant service restoration, user/config change or known quota reset may trigger recheck. Do not repeatedly probe unchanged auth/service blocks or treat old success as current blanket availability. BUSY and transient transport failures are scoped observations, not quota claims.

For WEB analysis bind selected file paths/hashes, task ID, sanitized prompt, source locator, recommendations, adoption/rejection and affected verification. Changed inputs invalidate affected recommendations. Never persist whole chats or secrets.

## Unambiguous task route resolution

The task template uses fallback.policy: inherit_project_default, explicit_order, or exclusive. Empty route arrays never mean permission to choose arbitrary software. Before READY resolve and record fallback.resolved_routes for this task_kind:

- inherit_project_default: resolve the invoking project's effective rules for this task kind. Record one actual primary and its authorized ordered fallbacks before READY, not an unresolved candidate list. Separate permitted routes from unavailable/skipped observations, recording reason and restoration conditions. Backend/design ownership also comes from that project's policy; preference is not evidence of tool access. If no applicable route can be selected within existing authorization, stay DRAFT and ask only for the missing decision. This repository's concrete choices are in [project-policy.md](project-policy.md); do not apply them to another project's existing or exclusive rules.
- explicit_order: use only the user-authorized ordered_routes for this assignment, nonempty before READY.
- exclusive: use exactly the selected executor/transport and no alternate. This overrides inherited defaults. Explicit user route restrictions take precedence over the template default.

Materialize the authorized chain even when an observation justifies skipping an unavailable route; separately record the attempted/skipped route and reason. Returning availability affects later tasks. Record use of specialist skills with native_skill/task_instructions/not_applicable plus supporting evidence; a listed name alone is not a load event.
