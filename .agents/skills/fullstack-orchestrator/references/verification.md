# Evidence and release scope

| Layer | Meaning |
|---|---|
| EXECUTION_DONE | Verifiable task termination/result record |
| ARTIFACT_VERIFIED | Actual files, write scope, build and affected module checks verified |
| INTEGRATION_VERIFIED | Predeclared business chain, contract, permissions/data and needed end-to-end paths verified |

Main defines acceptance before execution. A small docs/CSS change may need only narrow checks; cross-module business work needs the actual user-action → API/event → authorization/logic/data → response/history chain, including relevant failure/retry paths. Do not force databases, WebSockets, models or Docker into projects that do not use them.

Keep the agreed goal, write scope and acceptance visible. Record unrelated findings without automatically expanding the task; address defects that actually prevent the agreed outcome or are necessary dependencies. Once the applicable acceptance checks pass, finish rather than adding unneeded reviews or infrastructure. Report unverified items and genuine blockers instead of silently lowering acceptance.

Necessary dependencies do not override an explicit file/module or no-write restriction. Follow [task decisions](task-decision.md#决策顺序与范围冲突) when required implementation or verification exceeds that restriction. Generated files, caches, snapshots, test data and remote effects count as writes; a broader verification scope is not broader write authorization.

Scale checks to the actual change: LIGHT covers the relevant diff and focused checks; STANDARD adds applicable build, type, unit and interface checks; STRICT adds the necessary security, permissions, data, integration and recovery evidence for the risk. These are guidance, not substitutes for actual project requirements or the user's authorization. Evidence reuse never reduces checks required for a changed candidate.

Reuse project-native tests and installed quality skills. Record command, cwd, start/end, exit status, input/candidate identity and evidence location; absence of logs means absence of evidence. A worker's assurance is not acceptance. Risky auth/migration/security changes merit independent review; builds and generated mocks alone do not establish real integration. For UI verify actual interactions and relevant viewport/error/focus states when affected. Production has separate action-specific authorization.

| Gate | Required evidence |
|---|---|
| S0 static | Valid metadata, resolvable references, coherent scope/defaults, no duplicated specialists or fixed machine-path dependencies |
| S1 Codex application | Actual explicit-path loading and application to a bounded task: correct project/stack, specialist selection and missing-dependency behavior. Record catalog/automatic discovery separately; other-chat visibility is not required for this explicit path |
| S2 executors | Scope-specific real dispatch, artifacts, actual isolation limits, terminal detection and recovery for selected executors, including Stitch, authorized Antigravity routes, Gemini Desktop Task/Work, AI Studio Build or native workers; show C1/C2/C3 separately |
| S3 business | User-named real project/authorized isolated branch: business closure, contract/permission/data/UI/E2E, Git integration and applicable deployment recovery |

S0/S1 can justify STAGE READY with every missing desktop capability explicit. RELEASE VERIFIED requires all applicable S0–S3 evidence in the named environment/project scope. Never extrapolate to arbitrary future apps. If Gemini quota blocks C2/C3, keep S2 BLOCKED and S3 NOT_TESTED as appropriate; do not label Codex fallback output Gemini success.

When a concrete product task is supplied, derive the applicable runtime gates from the requested change. A selected external route requires current connection, grant, submission and artifact evidence. A frontend change requires the affected UI flow and contract checks. A business-impacting change requires affected real producer/consumer integration or user-flow checks in the named project; run full E2E only when the affected path or risk requires it. Do not require unrelated modules or an artificial interruption drill for a narrow change. An interruptible or delegated route requires an interruption or recovery check when resumption, fallback or uncertain termination is part of the task. A release request requires environment-specific deployment, health and rollback evidence after the required authorization. Skip a gate only when the task decision records `NOT_APPLICABLE` with a reason. The reusable Skill closeout may retain `NOT_TESTED` because it has no product task, but a product task cannot close an applicable gate as merely untested.

Record PASS, FAILED, BLOCKED or NOT_TESTED for each actual check; explain any not-applicable requirement. Record measured tokens/time/cost and interventions where accessible, else UNKNOWN. A local audit is not an app invocation, a scenario test is not an actual GUI handoff, and current-chat manual loading is not proof a different open chat's cached skill picker refreshed.

Environment/skill version changes trigger only relevant capability revalidation. Code/contract changes trigger affected regression checks. Deliver stage version, exact installed/package identity, configuration diff, evidence limits, usage instructions and rollback; no new release ceremony or controller service is needed.

## Current project materialization boundary

Project-local packaging and static validation do not verify any external route. CLI/Desktop/Work actual engineering, safe fallback, interruption recovery and business integration remain NOT_TESTED unless current scoped evidence exists. Historical blocked records remain historical and must not be rewritten as current observations. WEB analysis is advisory evidence, not executor success. Every affected route is checked only when selected; no all-services ceremony.

## Delivery and reopening

Use [closed-loop.md](closed-loop.md) for final requirement disposition, active-task reconciliation, authorized release, recovery and later defect handling. Reaching the agreed local deliverable closes that scope only; unresolved requirements remain explicit. Publish a current closure snapshot rather than rewriting historical blocker audits. Project-root selection is dynamic; do not resurrect obsolete absolute-path requests from old evidence.

## Requirement-to-evidence and review limits

For an actual assignment map each accepted requirement to affected artifacts, check IDs, result/evidence and unresolved decision. Cover only applicable business, UI, contract, permissions/data, algorithm and recovery behavior. Report NOT_APPLICABLE with reason rather than fabricating PASS. An incomplete requirement stays unresolved even if unrelated checks pass. An executed check can be reused only for the same candidate/inputs and affected environment.

Static metadata/link/template checks establish S0 only. Native read-only behavioral scenarios establish only the decisions exercised; no external dispatch, engineering or recovery claims follow. Current host catalog exposure establishes that this local skill is listed in this chat, not that other chats/software refreshed or loaded it. Record current host discovery separately from engineering invocation S1. Independent reviewers do not accept their own integration or grant authorization.

## Existing failures and regression attribution

For STANDARD/STRICT or otherwise medium/high-risk changes, state two separate review conclusions in the existing acceptance record: **requirements compliance** (accepted behaviors, scope, contracts, permissions and omissions) and **implementation quality** (correctness, maintainability, security/performance and regressions relevant to the change). Review the actual diff, relevant source and current check evidence, not only the implementer's report. One reviewer may cover both; use an independent reviewer when the risk calls for it rather than automatically spawning two agents. Tiny LIGHT tasks may keep a compact combined assessment.

A blocking issue in either conclusion prevents affected acceptance; fix and recheck it on the final candidate. Non-blocking findings retain rationale and disposition without expanding the task. Missing source or evidence gives a limited/INCONCLUSIVE conclusion, not PASS. These conclusions complement existing artifact/integration gates; they neither create permission nor replace runtime checks. On requirement or contract change, update only the affected requirement → producer/consumer/artifact → check mapping and invalidate dependent evidence; unchanged unrelated evidence remains reusable.

Capture relevant pre-change checks when needed to distinguish existing defects; do not rerun unrelated suites for bookkeeping. Compare the same command, inputs and affected environment against the final candidate. Classify each failure as pre-existing, introduced, unresolved attribution, or not executed, with evidence. A suspected old failure without comparable evidence remains unresolved; do not infer it from a familiar message.

New failures affecting the agreed outcome block acceptance. Unrelated baseline failures may remain documented outside scope if focused checks independently establish the requested behavior. If a baseline failure masks the required checks or business chain, report limited delivery/BLOCKED for that requirement instead of PASS. Do not delete, weaken or rewrite unrelated tests to obtain green results. Fix baseline defects only when necessary for the agreed goal or separately authorized, preserving the same change-protection rules.

Specification/tool checks, selected-client runtime evidence and product acceptance close separately. Product invocation verifies only applicable selected capabilities; no all-software rerun is required.

## Changed requirements and dependent evidence

When an accepted requirement changes, use the existing requirement/check map to name the changed behavior or contract, its direct producers/consumers and transitive dependent deliverables/checks. For example, changing an ID field's type can affect schema/validators, generated clients, UI callers, fixtures and integration checks even if their files have not yet changed. Keep old results as history; a matching source hash alone does not preserve PASS when the required behavior or test environment changed. Reaccept affected designs/contracts before dependent implementation, and recheck the final integrated candidate. A self-contained docs/style change does not invalidate unrelated backend evidence.

Record the reason and new requirement/input revision with each affected conclusion in native records; no new schema is required. Untraced consumers remain UNKNOWN with a coverage limit, not presumed unaffected. Do not remove a failing requirement, change its stage, or relabel it NOT_APPLICABLE merely to obtain PASS. Applicability changes require a substantive scope reason within current authorization; material product tradeoffs return to the user. Refer active attempts to handoff.md before sending revised instructions.


## Reusable Skill delivery records

When updating this reusable Skill, derive current test totals from structured runner outcomes rather than copying counts into requirement prose. Bind results to the tested candidate files and log hashes; a later relevant file change invalidates their reuse. Keep current checks, closure and verification on the canonical metadata version, with one backup pointer and a separate recovery policy; verify the backup's entry version. Preserve historical reports as historical. A passing archive byte check does not validate these semantic claims. This repository uses `tools/run_workflow_checks.py` and the read-only `tools/audit_workflow_delivery.py` at its project root; they are repository delivery tools, not assumed available in invoking product projects. Run the consistency gate and both archive integrity checks after final publication. A stopped release between archive/report replacements is an inconsistent pair: preserve the prior backup and rebuild/reverify; never infer rollback safety from a directory name or restore over live resource state.

For local reusable-Skill delivery, each required test suite must contain at least one actually passed test. An all-skipped suite is not passing evidence; retain skip reasons and report the missing verification. Package byte integrity is separate from semantic acceptance: require a nonempty canonical source manifest, reject ambiguous JSON integrity records, and never publish an archive or report over its input manifest.
