# Validate a delegated task record

Artifact file lists reject trailing directory slashes and file/descendant collisions such as `src` together with `src/app.py`. These are structural checks only: Main must still inspect actual file types, metadata and complete patch contents under handoff.md.

Use the JSON [task template](../assets/task-template.json) only when the product has no equivalent native format. Keep DRAFT while filling it. This helper is optional for native formats and narrow direct work; do not build a second task system merely to use it.

Run from the skill folder (resolve the actual folder, not the product cwd):

```sh
python3 scripts/validate_task.py /absolute/path/to/task.json
```

JSON uses Python's standard library. Existing YAML records are accepted only if PyYAML is already present; do not install it automatically. Exit 0 means VALID_RECORD, 1 means invalid structure, 2 means input/read/parse failure. A valid DRAFT remains DRAFT and cannot be dispatched. The command reads one record and writes JSON to stdout; it does not modify files, inspect apps, execute commands in the record or grant permissions.

UTF-8 input may contain a BOM; original bytes remain untouched. Duplicate object/mapping keys in JSON and supported YAML are rejected at every nesting level rather than silently taking the last value. YAML still uses a SafeLoader; ordinary merge-key defaults with explicit overrides remain supported. PyYAML remains optional.

For READY and later prepared states, fill source identity and dirty state, applicable contract/design identity (or an explicit reason for non-applicability), actual grants, deliverables, acceptance and submission/status/collection methods. Read-only work may have an empty writable_paths array; its actual_grants still describe the authorized read scope. Each resolved route is an object with software and transport; the selected executor must occur in the authorized list. Do not remove temporarily skipped routes from an explicit_order list: record skips and reasons in evidence instead. The helper does not choose routes or infer user authorization; Main must reject any route explicitly paused by the latest user decision, nonauthorized Gemini CLI/API and other disallowed routes even if a record is structurally valid.

Object sections must remain objects even in DRAFT. Required textual fields must be nonempty text, not booleans, numbers, whitespace or UNKNOWN. Required list fields must be nonempty.

executor.skill_mode accepts read_apply (actual local reading/application), native_skill (supported native loading), task_instructions (bounded instructions delivered to an executor), or not_applicable. Choose the actual mode; a structurally accepted value does not prove that loading occurred. skills_used may point to the existing detailed identity/use record rather than duplicating it.

In this template, inputs, writable_paths, actual_grants, deliverables, evidence and result.files contain nonempty text entries, not placeholder nulls, booleans or objects. Keep detailed file manifests or structured evidence in referenced records; equivalent native formats do not require conversion. Empty writable_paths is valid for read-only tasks; evidence and result.files can stay empty until the relevant completion claim requires them. limits.same_issue_repair_rounds must be an integer from 0 to 2, excluding booleans; it records the ceiling and does not enforce a live retry loop.

task_id 和 attempt_id 为单个安全目录名，可含中文，不得含路径分隔符、冒号、控制字符、首尾空白或 . / ..。result.files 为相对 result_location 所声明产物根的文件路径，不得为绝对路径、Windows 驱动器/反斜杠路径、含 .. 或控制字符；规范化后不得重复。这里只做字符串检查，实际符号链接、文件归属和访问授权仍由 Main 核对。

Each dependency records task_id, required_artifact, required_state, observed_state and evidence. Required states are EXECUTION_DONE, ARTIFACT_VERIFIED or INTEGRATION_VERIFIED; the observed state must meet that level. Main verifies the underlying artifact and current identity, rather than trusting those fields. Acceptance entries need check_id, requirement, method, verifier and required_evidence.

Every result.checks entry is an object with nonempty textual check_id, candidate_identity and evidence, plus a supported result. Optional stage is artifacts or integration; omitted stage defaults to artifacts for existing records. Artifact PASS requires at least one latest passing check bound to the current candidate. For each check_id recorded against that candidate, its latest artifact-verification result must be PASS or justified NOT_APPLICABLE; FAILED, BLOCKED and NOT_TESTED prevent artifact PASS. Checks from other candidates remain history and do not satisfy or invalidate the current candidate. Record deferred business integration checks with stage: integration; integration PASS also rejects unresolved or failed latest explicitly integration-stage checks for the current candidate. artifact acceptance does not imply that business acceptance passed. Keep checks in observation order: before recording integration PASS, the latest check for each acceptance check_id on the current candidate must PASS with evidence. An earlier PASS cannot hide a later FAILED check. Retain failed commands/attempts in the project record; a subsequent candidate-bound successful check does not erase them. Unsupported cancellation/resume remains UNKNOWN or justified non-applicability. UNKNOWN_EXECUTION records need a blocker and next action and cannot claim PASS for the same attempt.

Limit: strings and evidence pointers are declarations. This helper cannot establish real filesystem grants, artifact existence/content, accepted business decisions, task termination, truthful logs or engineering success. Main performs the source, app, permission and final-candidate checks in [handoff](handoff.md) and [verification](verification.md). These checks do not implement a state-transition engine or exactly-once dispatcher. For analysis-only tasks, keep non-applicable artifact/integration outcomes with a reason rather than claiming integration PASS without files.

Run the helper's synthetic regression checks after changing it:

```sh
python3 -m unittest discover -s scripts -p 'test_validate_task.py' -v
```

These fixtures never count as Stitch/Gemini/Antigravity capability or product acceptance evidence.

## Record versions and layered acceptance

New template records use integer `schema_version: 2`. Omitted version is legacy 1; explicit 1 is accepted. Other versions and noninteger values are rejected. This format version is separate from the Skill release version. Do not rewrite historical records merely to migrate them. Version 1 preserves unstaged acceptance behavior: those items are enforced at integration acceptance, not inferred to be artifact requirements. An explicitly staged v1 item uses that stage. For an active v1 task, Main must still check the agreed artifact acceptance; legacy structural compatibility does not waive verification. To adopt v2 deliberately, classify each existing acceptance item and revalidate; do not blindly add a version number.

Version 2 requires every acceptance item to declare `stage: artifacts` or `stage: integration`. Artifact PASS requires every declared artifact-stage item to have a latest PASS bound to the current candidate and stage; an unrelated PASS cannot substitute. Integration PASS requires all declared acceptance items to PASS in their matching stage. Missing check stage still defaults to artifacts for compatibility. Required acceptance cannot be closed by marking its result NOT_APPLICABLE; deliberately revise applicability/scope with a reason before claiming acceptance. Supplementary checks may remain justified NOT_APPLICABLE. Deferred integration checks do not block artifact acceptance.

Inputs are nonempty text references when present, with source identity/hashes in the referenced manifest; empty inputs are allowed for tasks with no supplied files. This check does not resolve paths or validate those hashes. DRAFT may leave IDs null, but supplied IDs must be safe strings; false, zero and empty values are not unset IDs.

Route identity is the exact software/transport pair. Optional reason/evidence metadata does not change identity. Duplicate identities are rejected; explicit ordered routes preserve pair order. This does not normalize product aliases or grant route authorization.

FAILED may retain successful earlier layers, but cannot claim integration PASS for the same attempt. CANCEL_REQUESTED/CANCELLED cannot claim execution PASS: if completion won the cancellation race, retain EXECUTION_DONE or its verified successor and record the late cancellation request in evidence. Cancellation here is a record convention, not proof that a provider stopped.

For schema v2, integration PASS also requires at least one declared integration-stage acceptance item with current-candidate passing evidence. A task without integration scope may finish at ARTIFACT_VERIFIED; it must not claim integration PASS solely from artifact checks.

Full integration PASS is valid only with lifecycle INTEGRATION_VERIFIED. A later blocker, cancellation or new scope belongs in a separate attempt/change record; earlier execution/artifact success may remain recorded when integration fails or is not applicable.
