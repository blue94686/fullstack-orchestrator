# Submission, observation and collection protocol

Use actual supported tools and existing project records. This document specifies records/actions, not an executable adapter, universal CLI flags or an installed scheduler.

Use available native subagent tools for bounded Codex workers in this chat; do not create a separate user-owned chat merely to delegate. For external software prefer a connected, suitable provider tool when the selected route permits it; otherwise use supported desktop control with current app observations. Discover tools by their actual advertised capability before selecting them. A browser-only connector cannot establish native desktop control, and a tool name mentioned in a handoff cannot create that tool. Missing access blocks only the affected task. Do not invent CLI flags, MCP calls, task handles or a bridge service to fill an absent integration.

## Minimal executor capability record

For a selected route record the [capability matrix](connection-capabilities.md): software/transport; actual configured model when exposed; version when observable; observation time; requested capability; actual tool/folder grants; task handle or unique locator; submission/status/artifact/cancel/resume methods actually available; evidence; blocker; recheck trigger. Absent values are UNKNOWN. Separate NOT_TESTED from BLOCKED (an observed preventing condition) and NOT_APPLICABLE (reason required).

**READY is prohibited until every dispatch-required capability has current evidence for the exact product root/workspace, account/service, client/transport, mode, grants and input revision.** Dispatch-required means the methods, bindings and permissions needed to start and safely attribute the selected stage. For first-use clients, follow the bounded capability-check stage in connection-capabilities.md; actual read/write/execute results remain NOT_TESTED until performed, and dependent engineering stays DRAFT. Later lifecycle operations are gated when reached. Do not demand successful submit/export/cancel/resume/integration evidence before the relevant action has happened. If a material recovery limitation makes dispatch unsafe, keep DRAFT or mark BLOCKED for an observed prevention. If a binding changed or cannot be observed, resolve it before READY. Invalidate only the capabilities and checks affected by that change; retain unrelated evidence as scoped history. A prior PASS for a different directory/account/client/input cannot satisfy this gate.

Never infer Gemini Work file execution from its mode name. Confirm the intended mode, actual task workspace and ability to produce retrievable files/check output. If only conversational suggestions are possible, that is advisory capability, not a frontend engineering fallback. Report the missing capability; use another executor only if authorized.

CLI executable presence/help is discovery, not a working model. Read actual supported options and preserve model/effort/auth; do not invent command flags. App launchers are not coding-agent CLIs. For Desktop use fresh observations and supported control; for MCP verify the actual applicable connection. Do not silently substitute transports with a different permission or billing profile.

## One task, one controlled attempt

1. Prepare: check DRAFT→READY requirements, baseline, dependencies, no live/unknown duplicate, folder grants, ownership, timeout and permitted fallbacks. Reuse sufficient valid observations.
2. Submit: persist task/attempt/locator mapping using project-native records. DISPATCHING is not RUNNING. Read back target folder/prompt; submit once. If receipt fails, reconcile the possible submission before changing software.
3. Observe: use native task/process handles or existing app task state. Separate Main's tool wait timeout, task deadline and confirmed provider termination. Poll sparingly; do not infer liveness from an old lock/time or promise wakeups absent a real mechanism. Releasing the GUI does not prove the app task stopped.
4. Collect: confirm the corresponding terminal attempt, or a supported, identifiable delivery/export event whose delivered file set is closed to further writes; preserve real files/patches, exported designs, commands, relevant logs and unresolved issues. A chat reply can deliver an advisory task, but code execution needs file artifacts and applicable checks.
   A closed delivery event permits collection and verification of that set only; it does not mark a still-running attempt EXECUTION_DONE or permit replay. Keep the attempt at its observed lifecycle state until termination is confirmed.
5. Verify and integrate: inspect scope/permissions/contract drift and compare to baseline; run affected final-candidate checks; either accept the required layer or assign a bounded repair. See [handoff](handoff.md) and [verification](verification.md).
6. Suspend/resume: save minimal IDs, locators, candidate and next action. Resume verifies actual state first. No new daemon, recurring automation or whole-chat archive is required.

Main or a delegated controller may operate the GUI, never both simultaneously. Main retains the task record and shared GUI ownership before another controller takes over. A prompt label is not a robust distributed lock; no exactly-once guarantee is implied.

## Failure and fallback decisions

Every generic fallback below is subject to the task route, routing.md and current project-policy.md. Current temporary unavailability does not erase the long-term CLI-first preference or authorize probing an unchanged blocker. Codex may be selected at the task boundary under task-decision.md. In an authorized Antigravity chain, CLI technical failure permits evaluating Desktop; Gemini fallback requires confirmed whole Antigravity unavailability. Single-client BUSY, quota or missing Stitch MCP alone does not establish that. Unknown submission requires reconciliation before any alternate dispatch. Never use a generic table row to bypass an exclusive route.

| Observation | Decision |
|---|---|
| missing/unsupported CLI or transport failure before known submission | allowed Antigravity Desktop route; keep scope/grants and record reason |
| whole service confirmed unavailable | skip its transports; independently available Gemini Work may take authorized work |
| Authentication/service/policy denial | no retries or transport/account/proxy workaround; record recheck condition; independently authorized other service can do permitted work |
| Quota/transient failure | preserve actual reset/retry hints if exposed; bounded retry or allowed independent fallback only after side effects are reconciled |
| BUSY on unrelated task | do not interrupt or inspect it; defer or use permitted route; independent tasks continue |
| Submit uncertainty/timeout/cancel unconfirmed | UNKNOWN_EXECUTION; reconcile the original attempt, block replay |
| Build/test failure | bounded diagnosis/repair; do not call it software unavailability |
| Contract or user-file conflict | preserve files; Main resolves within scope, asks only for unresolved material decision |
| All allowed frontend routes unavailable | block dependent frontend/integration; continue independent authorized backend work |

### Partial success, disconnection and unconfirmed cancellation

Use this decision table together with [handoff recovery](handoff.md#reconcile-before-replay). It applies even if another client is available or a deadline is near.

| Observation | Record and contain | Resume/fallback rule |
|---|---|---|
| Request may have been submitted but no attributable receipt/status | `UNKNOWN_EXECUTION`; retain original attempt/locator and do one bounded read-only reconciliation | No replay or overlapping writes until same attempt is reconciled |
| Timeout/network loss after confirmed submit | Keep last observed execution status; if current status cannot be recovered, `UNKNOWN_EXECUTION` | Preserve partial outputs and stop additional writes to overlapping paths; independent tasks continue |
| Cancel requested but no confirmed terminal status | `CANCEL_REQUESTED` only while request status is observable; otherwise `UNKNOWN_EXECUTION`; record request separately from termination | No replay or overlapping writer while execution is unconfirmed; a supported closed delivery set allows collecting that set only and does not release the running attempt |
| Some expected artifacts exist but the task is not terminal and delivery set is not confirmed closed | Keep them in the original attempt as partial/unaccepted; artifact and integration outcomes remain not passed | Do not collect as complete or have another route modify the same paths |
| Quota, auth or policy denial after an attempt may be running | Record denial for the new request and preserve the original attempt's status uncertainty | Denial does not stop the original attempt; never switch transport/account/proxy to evade policy |
| Confirmed terminal failure/cancellation with side effects reconciled | Keep the failed attempt and partial artifacts; diagnose the smallest failure and idempotency | A new authorized attempt may start only after checking side effects, revised inputs and allowed route; same-issue auto-repair ceiling still applies |

For any ambiguous case: freeze only conflicting writes, preserve evidence, reconcile the original attempt, establish whether effects are idempotent/compensated, then decide. Do not auto-delete partial files, reset user changes, rollback migrations or assume code rollback reverses data. Ask for a decision only when recovery is destructive, business semantics are unresolved, or new authorization is required; continue independent authorized work.

Transport observation retries and code repairs have different budgets: declare a small attempt/deadline limit for transient connection/status reads, honor actual retry hints without busy polling, and stop when exhausted. An unchanged auth/policy denial is not transient. Each write/submit retry first reconciles the prior side effect; never use a transport retry budget to bypass the logical task's two automatic same-issue repair limit.

A service becoming available affects future dispatch, not an active attempt. Cache scope/capability/reason/evidence/recheck trigger in project records; no blind periodic retries of unchanged denial.

## Bounded fast path

For a connection check or small follow-up, keep one compact scope, route, stopping condition and result in chat; create persistent records only when execution, recovery or handoff needs them. Read only the relevant reference sections and changed files. Reuse evidence with matching source, client, permissions and scope; an affected change invalidates only the affected evidence. Do not reread entire histories, run unrelated audits, launch design software or repeat product E2E merely to check a CLI.

Separate interface discovery (`--help`) from a real model call and from engineering verification. When a live probe is authorized and needed, prefer one bounded nonsecret response with a declared deadline (normally 30–60 seconds for a connectivity probe), supported timeout/output options and no product writes. Slow startup may leave the result inconclusive; inspect the original task before any retry. A process timeout never establishes remote termination. Use an explicitly bound conversation for follow-ups; avoid unqualified “continue latest” when multiple projects or tasks exist. CLI-first applies only when that route is authorized and callable.

A user reporting software temporarily unavailable pauses further probes, including alternate transports, until a new recovery signal and applicable authorization. Do not silently unpause a persistent route because an executable exists. Continue independent work where useful.

Keep prompts and returned evidence proportional: pass file pointers plus changed constraints in an already bound workspace; request a short result and necessary artifact paths, not a restatement of the full task. Preserve matching task terminal-state checks and affected verification. Measure elapsed time per probe when available; report provider token/cost usage only if exposed. Goal-wide cumulative accounting is not per-call billing and must be labeled separately. Reduced overhead is an intended effect, not a measured saving without comparable measurements.

## Evidence retention and data

Store only necessary sanitized evidence and stable locators; exclude tokens, credentials, signed URLs, entire chats and unrelated files. Reuse project ignore/access rules; do not silently change repository sharing or retention policy. Record source identity and output pointers; do not invent historical timestamps/raw logs. For design exports without provider version use file hashes and record the limit. Time/token/cost unavailable means UNKNOWN.

## Participating single-host projects

Before development or GUI side effects use [local coordination](local-coordination.md) to acquire all needed resources atomically, retain the project-local grant binding and check it before controlled actions/integration. Resource waiting is a scheduling disposition, not a new task lifecycle state. Process exit/timeout does not terminate execution or release persistent grants. GUI observations and actions are serialized across the user desktop; background execution retains its separate development/client/workspace grants. No automatic wakeup or enforcement over nonparticipants is provided.
