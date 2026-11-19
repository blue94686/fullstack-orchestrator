# Task contract, integration and recovery

Use the active product project's own task/checkpoint records. The exchange directory is created dynamically at that project's root-relative `shared/` path, with ownership and exchange rules in its `shared/README.md`; this repository's `shared/` is only the local project's instance and must not be copied as a fixed absolute location into another project. Keep task records there instead of introducing a parallel `.ai-workflow/`. For other projects without equivalent records, create the same minimal `shared/` structure when file exchange is required; do not introduce a queue, database or daemon. Exclude sensitive logs and caches from version control.

Each delegated task records:

- Unique task ID and attempt ID; actual executor and owner.
- Goal/non-goals; repository/workspace and approved writable paths; actual tool/folder grants.
- Baseline commit plus dirty state and hashes of relevant inputs; contract/design versions.
- Expected files and result location; exact acceptance scope, commands and responsible verifier.
- Timeout, at most two same-issue repair rounds, available usage budget, selected executor, dependency links and any authorized fallback with its conditions.
- Lifecycle status and separate execution/artifact/integration outcomes; timestamps and evidence pointers.
- For an external task, link logical task/attempt to its actual app and transport and, where exposed, task/thread or project/screen ID; otherwise retain a unique searchable locator and submission time, noting ambiguity. Redact credentials, signed query parameters and private content from locators. Record the latest observed status/time and evidence location without saving full conversations.

For transition guards, cancellation, reopening and final delivery see [closed-loop.md](closed-loop.md). These are control rules, not runtime-enforced transitions.

Suggested lifecycle: DRAFT → READY → DISPATCHING → RUNNING → EXECUTION_DONE → ARTIFACT_VERIFIED → INTEGRATION_VERIFIED. FAILED/BLOCKED/UNKNOWN_EXECUTION/CANCEL_REQUESTED/CANCELLED may occur at any applicable step. Keep each outcome rather than overwriting a failed build with “worker finished.” NOT_TESTED means no current verification; not-applicable needs a reason, not PASS.

Before dispatch, check relevant existing native task handles or checkpoints for the same logical task across all executors and attempts. If a matching attempt is active or its outcome is unresolved, reconcile that attempt instead of submitting a duplicate. Record current files/Git state and task ID. Give only necessary files, interfaces, permissions and acceptance. For a durable excerpt or handoff package, bind the exact selected source paths and full-file hashes to the task; recheck relevant sources before dispatch and before relying on the package. If an input changes, inspect the impact and update the handoff deliberately, not silently. Hashing or an allowed-path prompt is evidence, not an access-control sandbox. Workers cannot change shared contracts or accept their own integration.

## Main's integration authority

Check changed/untracked files against allowed scope; preserve user dirty changes and other workers. Inspect diff and contract/lockfile compatibility. Run affected project checks against Main's candidate unless valid evidence already covers that exact candidate, inputs and scope. Resolve mechanical conflicts only when semantics are clear; a permission, business or contract conflict returns to Main's decision within user authorization. Never use reset/force checkout to make a merge appear successful.

Before writes and again when collecting/integrating, reconcile relevant user changes, workspace ownership and shared-contract drift. Resolve symlink targets for scoped paths before using them; do not follow a link beyond actual authorized access. If a concurrent change makes attribution or safe integration uncertain, preserve it and stop affected writes until reconciled. These checks do not enforce an OS sandbox.

## Reconcile before replay

The combined timeout/partial-output/unconfirmed-cancel case is summarized in [operations.md](operations.md#partial-success-disconnection-and-unconfirmed-cancellation). In particular, a fallback client must not write overlapping paths while the original attempt may still be active, even when quota or connection failure prevents further requests on the original route.

1. Load the last checkpoint, task/attempt IDs, current app/tool status and workspace baseline.
2. Locate the same external task and attempt via its recorded mapping. Check live status using a real provider/tool handle, relevant process or application state when available, as well as actual files, diff, logs and candidate identity. A receipt, old timestamp or lock alone does not establish liveness or termination. A confirmed live task is observed or resumed through its supported mechanism; never submit a duplicate. Terminal task + correct outputs → validate them.
3. If execution outcome is uncertain, set UNKNOWN_EXECUTION. Do one bounded read-only reconciliation. If identity or liveness remains uncertain, block replay and report the missing observation; do not guess the task, create a duplicate, clear a lock, kill a process or take over an active coordinator based only on elapsed time. Recheck the same known live handle when justified.
4. When failure is confirmed, preserve artifacts and reproduce the smallest failure. Determine whether retry is idempotent or needs a new attempt after reconciled side effects. At two unsuccessful automatic repair rounds stop that issue and report it; independent work may continue.
5. A changed source/contract invalidates only affected prior evidence. Re-run corresponding checks against the final candidate; historical successes remain historical.

On a confirmed unavailable executor, propagate BLOCKED to tasks depending on its missing output, not to independent tasks. Fallback selection follows routing.md; keep the original attempt and actual executor in the record. Never create a fresh attempt or alternate route merely to hide an unknown result, denied permission or exceeded scope.

Stopping further dispatch, requesting cancellation, and confirmed cancellation are distinct. Do not claim an external task was cancelled merely because a request was sent or a wait ended; if termination is unconfirmed keep UNKNOWN_EXECUTION and reconcile through the supported handle. Do not assume an executor offers cancellation or resume.

For a safe recovery test use scratch task records or an existing authorized isolated branch, not a new product/webpage. Exercise interruption/duplicate dispatch, failed test and Git conflict without touching production or consuming paid external tasks solely for simulation. A simulated policy response is not a real desktop C3 pass.

## Long-term checkpoint

Keep only durable decisions, running and uncertain task/attempt IDs plus their external locator mapping, completed IDs, commit/candidate identity, relevant environment versions, accepted contracts, unresolved items and next action. Reuse README/AGENTS/ADRs and existing AI-SDLC records. Do not persist whole chats, credentials or personal memory. On resume verify actual state before trusting the checkpoint. Back up only configurations authorized for change; rollback restores the prior exact files without replacing unrelated edits.

## Submission and artifact completeness

DISPATCHING means submission began but receipt is not yet confirmed. No feedback is UNKNOWN_EXECUTION, not evidence of no submission. Every dependency names required artifacts and its minimum accepted state. Retain separate execution/artifact/integration outcomes, original failed attempts and only affected evidence invalidation. These rules reduce duplicate side effects; they do not provide an exactly-once runtime guarantee.

Frontend handoff includes real source, page/action mapping, API method/path/fields/errors, ownership/permission requirements, mock boundaries, start/check commands, design identity and unresolved questions. Backend handoff includes implementation or patch, contract differences, migrations if applicable, checks and integration method. Design handoff includes actual exports and identity; screenshots alone do not establish source availability. Shared contract changes name reasons, affected consumers, compatibility and rechecks; Main accepts and coordinates them.

## Readiness, revisions and integration rejection

An empty template is DRAFT. READY requires an identified task/attempt and repository, a selected executor and materialized permitted fallback.resolved_routes under routing.md (no ambiguous empty inheritance), relevant source/contract/design identity, dependencies satisfied to their declared level, actual grants and write ownership, a result location, acceptance and available submission, status and collection methods. Unsupported cancel/resume may be UNKNOWN or NOT_APPLICABLE with reason; they are not universal readiness prerequisites. Unfilled or unselected inputs stay DRAFT; an evaluated external preventing condition is BLOCKED with a reason and next trigger. Do not dispatch unresolved business assumptions merely to fill missing fields. Record justified not-applicable fields for narrow tasks.

If a scope/contract change affects an active attempt, stop new dependent dispatch, preserve its files, and request cancellation only if appropriate. Wait for confirmed terminal state or retain UNKNOWN_EXECUTION; then create a new attempt from reconciled inputs. Invalidate only affected verification. An integration rejection does not erase execution completion: record the failed check, assign a bounded repair, and retain all attempts and candidates. Final acceptance is against the integrated candidate, not the worker's isolated branch.

Before applying patches or importing files, compare actual current user changes and the baseline. Missing immutable app versions can be replaced with hashes of actual exports, with limits recorded. In non-Git projects use explicit file manifests/diffs; never invent a commit or initialize Git merely to satisfy the template. Rollback preserves unrelated later edits.

## Ownership and complete collection

For product/worktree/exchange mapping, cross-chat coordination, takeover and complete artifact collection use [execution boundaries](execution-boundaries.md). A timestamp or lock expiry is not termination. A completion manifest is not acceptance. When an executor cannot supply one, Main may manifest a stable snapshot only after an observed terminal or supported delivery event. Record the provenance; do not integrate partially written files.

When exchanging patches, name the patch base and intended destination, then account for additions (including untracked files), modifications, deletions, renames, binary assets and relevant executable/type changes. A plain working-tree diff can omit staged or untracked content; a textconv/review rendering is not necessarily an applicable patch. Collect necessary bytes and metadata using existing project tools, scoped to authorized paths. Do not stage user files merely to make a complete diff. Treat ignored files, submodules and links explicitly when relevant; do not recursively collect ignored credentials or expand access through links.

Check applicability against the reconciled destination before mutation (for Git patches, use supported read-only apply checks), then inspect the integrated result and run affected checks. Failed application is not permission to force, fuzzy-apply or overwrite user edits. A deletion/rename requires attribution and scope just as an edit does; a missing exported file is not itself a deletion instruction. File manifests must not name a directory as a file or name both a file and its descendant. Byte hashes alone do not preserve executable bits, link targets or deletion intent. If a format omits necessary metadata, record and verify it separately; the workflow delivery ZIP normalizes regular files to mode 0644 and does not promise full filesystem restoration.

## Incremental context and artifact index

For a resumed external task, first reconcile the original attempt as above, then send only the delta: task/attempt and candidate identity; changed inputs/contracts and their identities; invalidated conclusions/checks; remaining action, allowed writes and acceptance. Ask the executor to acknowledge the changed baseline before dependent writes. Reusing a conversation does not preserve validity of old instructions. If its context is demonstrably unusable, first establish termination or safe read-only status of the old attempt, record the reason and locator, then use an authorized new conversation with a compact checkpoint. Never copy full chat history by default.

Keep the active brief authoritative in existing task records: accepted goal/non-goals, current input/contract revision, writable scope and prohibitions, unresolved facts, acceptance and next action. A delta identifies which prior instruction it supersedes; do not leave incompatible old and new briefs both active in a reused conversation. The receiver acknowledges the effective revision and boundaries, not merely “received.” A stale or conflicting receipt blocks dependent writes until clarified. This is an instruction protocol, not proof that a client paused or enforced it; reconcile already-running work first. Distinguish verified facts from assumptions/UNKNOWN when compacting context, and retain authorization limits even when dropping implementation history.

Count the same-issue repair ceiling across attempts, executors and conversations of the logical task. Record the smallest reproduced failure, proposed cause, actual changed variable and observed result. Changing route/attempt does not reset the ceiling; do not replay a known failing action without new evidence or a relevant change. After the ceiling, stop that repair dependency and report the evidence and remaining decision while independent authorized work continues. Distinct failures are classified by cause and evidence, not renamed to evade the ceiling; further rounds require a user decision or materially new evidence that justifies a new scoped investigation, not automatic cycling.

For long or multi-attempt tasks, keep a small index in existing project-native records, or `shared/tasks/<task-id>/INDEX.md` if no equivalent exists. Main alone maintains task ID, current attempt(s) and owner, latest observed state/time, external locator, candidate/input/contract identities, accepted artifact paths plus hashes, superseded attempts/reasons, unresolved side effects and next action. Main is the single record writer. Publish task/index changes via same-directory temporary file plus atomic replacement when supported; flush durable checkpoints as the project requires. Check the last accepted revision before replacement, preserve prior attempts, and do not partially overwrite a record. Corrupt/truncated or stale records are not evidence of an idle task: retain them, reconcile the actual handle and recover from a verified prior revision without erasing newer execution. No new record-store service is implied. An index points to authoritative attempts/evidence; it cannot overwrite their history or prove liveness. Concurrent independent attempts remain separately listed; UNKNOWN is never silently replaced with a new active attempt. Short direct tasks need no index. Do not auto-delete older artifacts or store credentials.

Before dispatch and collection, check the relevant paths and source identities using actual tools, inspect attributable changed/untracked files (or baseline hashes without Git), and verify returned files and referenced evidence exist. If no reliable baseline covers a path, report that attribution limit instead of claiming all writes were within scope. An evidence hash proves bytes, not truth or business sufficiency. Follow the existing integration and closure gates; these checks neither enforce a sandbox nor prove exactly-once execution.

## 本机资源绑定

参与单机多项目协调时，按 [local-coordination.md](local-coordination.md) 将每个实际执行者/GUI 操作的稳定 operation、资源、授权令牌与代次绑定在本项目原生私有记录中；不要把令牌提交或传入外部提示词。已有 JSON 模板不因此强制换 schema，可采用等效旁记录。资源获取/释放结果与执行状态、验收分别记录；幂等 acquire 不是重新提交指令。恢复前核对原授权和真实任务；失联不自动释放。

## Dispatch and collection identity gate

发送前与收集时都匹配产品真实根、执行 workspace/相对映射、task、attempt、输入 revision/原始字节哈希、基线和契约版本；会话 locator/角色与当前软件目录也核对。文件存在、相同任务名或会话显示名不足以确认归属。发送后先取得有效边界回执；收集后独立检查实际文件/diff。错项目、旧输入、契约不符或不完整产物先进入所属 attempt 隔离区，标记拒收原因，禁止直接覆盖当前工程；变化的依赖证据进入待复核。归属未知时只在当前收集项目的已授权最小隔离区保存，标记 origin=UNKNOWN；未确认来源与授权前不向另一项目写入或复制内容。revision 或哈希任一不匹配均先隔离；Main 核实影响后可记录等价/再利用决定，不能仅凭同字节或同版本标号自动接受。

单一写入者可在已授权原项目直接最小修改，保留用户未提交内容；多个写入者优先使用隔离 worktree/产物目录，并分别声明实际可写工作区，由 Main 集成。不能因并行而自动重建项目，也不能用锁代替真实写入隔离；没有可验证隔离时串行写入。同项目同角色会话可跨已结束任务复用，但执行互斥与独立 attempt 不合并。
