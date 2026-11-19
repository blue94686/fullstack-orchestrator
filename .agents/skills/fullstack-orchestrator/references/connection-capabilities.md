# Connection capability evidence

Use this only for a selected external client, provider, transport, integration or required project resource. It is a per-task evidence record, not a connection manager or permission grant.

## Capability matrix

Record each capability separately; do not infer one from another. `PASS` means an observed operation succeeded for the exact recorded binding. `BLOCKED` requires an observed prevention and reason. `NOT_TESTED` means there is no current attempt. `NOT_APPLICABLE` requires a reason. Missing or ambiguous values are `UNKNOWN`.

**Gate by lifecycle stage.** Before dispatch, require only the capabilities needed to start safely: discover/select the route, authenticate or observe existing authorization where applicable, confirm input delivery, actual grants, supported scoped read/write/execute methods, and a way to attribute or reconcile submission/status. Actual read/write/execute results are gated as described below. `submit` cannot be PASS until submission occurs. `export`, `cancel`, `resume` and `integrate` are gated when those actions are reached or when the task requires them; do not demand successful cancellation/recovery before starting ordinary work. If an essential post-submit capability (for example, no way to determine whether a timed-out task is still running) is absent, record the recovery limitation before dispatch and choose a safer route or keep the task DRAFT/BLOCKED according to risk. This is a readiness and evidence policy, not a requirement to exercise destructive or optional operations as a preflight.

| Capability | Evidence required |
|---|---|
| discover | Exact executable/provider/app/tool identity and supported operation; discovery alone does not prove execution |
| authenticate | Current nonsecret account/service identity and successful authorized request; never record tokens |
| read | Read the specific assigned input under the current project/workspace mapping |
| write | Create or edit one allowed test/task artifact and independently observe its bytes |
| execute | Run the task's required command/check in the intended workspace, with output and exit status |
| submit | After dispatch: one attributable task submission with actual receipt/locator; intent or button click is insufficient |
| status | Retrieve current state for that same task/attempt via a supported handle or observed app state |
| export | When required: produce the requested artifact locally/cloud-side and verify the exported file set and identity |
| cancel | When cancellation is requested: independently observe confirmed termination; an issued request is not PASS |
| resume | When resuming: verify same task/attempt, effective input revision, scope and current state |
| integrate | When integration is in scope: Main applies/reconciles the returned candidate and verifies affected checks; worker completion is insufficient |

Design resources (Stitch/Figma) need their own read/inspect/export capabilities. A connected model does not imply design-service access. A cloud preview or export does not imply access to local `shared/` or local project files.

## First-use capability check

A client that executes only after Task submission must not be required to have already executed that Task. Distinguish **observed support and authorization** from **successful operation**. A visible menu or documented method is discovery evidence; `read/write/execute` remain NOT_TESTED until their actual results are independently checked.

When current login, exact workspace/grants, supported methods, attributable submit/status/collection, no duplicate attempt and required resource ownership are confirmed, Main may make a **bounded capability-check stage** READY within the authorized task. Declare its exact input, scratch artifact path, harmless command, stopping point and evidence before submission. Use the existing role conversation and task/attempt; this need not create another conversation or a second parallel task. If the client cannot reliably stop before implementation, submit a separately bounded probe in that same conversation and keep the engineering stage DRAFT. A probe is not permission to touch product source, install dependencies, contact additional services or expand folder access. REVIEW does not permit a write probe without separate authorization.

Submit once, reconcile its locator, then independently inspect actual input identity, artifact bytes, cwd, command output/exit status and the matching task state. Only after needed capabilities succeed may Main activate the dependent engineering stage. Failed/ambiguous probes block only dependent work; an uncertain submission follows UNKNOWN_EXECUTION and cannot be repeated on another route. Prior evidence may replace the probe only for the same still-valid binding. Record this bootstrap scope and NOT_TESTED capabilities explicitly; never label the full engineering task READY merely because the probe is READY.

Use explicit per-stage states in native records. If the selected record format supports only one lifecycle (including this Skill's JSON task template), keep the engineering record DRAFT and use a linked, narrowly scoped probe record for READY/dispatch. Reuse the role conversation, reconcile its active attempt first, and serialize both stages; a linked probe is not a duplicate engineering dispatch or permission to open a fresh conversation.

## Minimal record

Use project-native task records. Do not force a second schema where an equivalent record exists. For an external capability observation capture:

```yaml
executor: <software/client>
transport: <actual transport>
model: <actual configured model or UNKNOWN>
client_version: <observed version or UNKNOWN>
account_scope: <nonsecret account label or UNKNOWN>
project_root: <resolved product project identity>
workspace_mapping: <execution workspace to project-relative paths>
mode: <observed mode>
grant_scope: <actual folder/tool grants; UNKNOWN if not observed>
capabilities:
  read: {result: NOT_TESTED, evidence: null}
  write: {result: NOT_TESTED, evidence: null}
  execute: {result: NOT_TESTED, evidence: null}
  submit: {result: NOT_TESTED, evidence: null}
  status: {result: NOT_TESTED, evidence: null}
  export: {result: NOT_TESTED, evidence: null}
  cancel: {result: NOT_TESTED, evidence: null}
  resume: {result: NOT_TESTED, evidence: null}
task_id: <logical task>
attempt_id: <attempt>
locator: <redacted stable locator or UNKNOWN>
observed_at: <actual time>
recheck_triggers: [<relevant changes>]
limitations: [<what this evidence does not prove>]
```

Store only fields relevant to the selected route. Do not place credentials, signed URLs, full chats, private source, or unrelated user data in the record. Reference evidence by project-relative path and hash when useful.

## Freshness and invalidation

Before READY, the selected stage must meet its dispatch gates for the current binding, including the bounded first-use exception above; later lifecycle capabilities remain NOT_TESTED until reached. A material binding change invalidates affected evidence; it does not invalidate unrelated evidence. Recheck only what changed and what depends on it. There is no universal TTL and no evidence is permanent merely because it has no expiry.

| Change observed | Recheck or invalidate | Evidence normally retained |
|---|---|---|
| product root, checkout, worktree or path mapping changed | project identity, path resolution, input identity, read/write scope and artifact location | unrelated app login or export format only if independently bound and still observable |
| folder grant changed, revoked or uncertain | read/write in the assigned folder and actual scope; no READY until sufficient grant is confirmed | model identity and unrelated service capabilities |
| account, tenant or service identity changed | authentication, policy/access and each protected operation required | local path mapping if unchanged; never assume account equivalence |
| client, plugin, MCP server, extension or tool config changed | affected discovery, submit, status, read/write/execute/export/cancel/resume methods | independent unchanged capabilities with their own evidence |
| model or inference settings changed | record actual model/settings and re-evaluate output-quality checks that depend on them | filesystem permissions and task locator when independently unchanged |
| client version changed | affected operation support and behavior; preserve exact old evidence as history | unaffected independently observed grants, subject to current UI confirmation |
| task input, contract, design or acceptance revision changed | acknowledge revised brief, hash the new inputs, invalidate dependent output and checks | unrelated task capabilities and unaffected checks |
| network, quota, BUSY or service denial | current affected request and retry/fallback eligibility | prior successful operations as historical evidence; no inference that a running task terminated |

If a required start method, binding or authorization is UNKNOWN, stale or merely inferred, do not mark that stage READY. A first-use operation result may remain NOT_TESTED only inside the bounded capability-check stage above; dependent engineering remains DRAFT. Keep it DRAFT while facts are being gathered; use BLOCKED only for an observed preventing condition. Do not probe unchanged denied services repeatedly or switch transports to evade policy.

## Evidence boundary

Connection, permission, file exchange, engineering execution, artifact integrity, integration and product acceptance are distinct claims. Record only the highest layer actually observed. `read` plus `write` in a scratch folder does not prove source-code execution; a successful build does not prove business integration; a screenshot does not prove editable design source; a timeout does not prove termination. Follow [operations](operations.md), [handoff](handoff.md) and [verification](verification.md).
