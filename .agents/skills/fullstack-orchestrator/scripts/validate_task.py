#!/usr/bin/env python3
"""Read-only structural checks for orchestration records, never runtime acceptance."""
import argparse
import json
import sys
from pathlib import Path
import re
import unicodedata

STATES = {"DRAFT", "READY", "DISPATCHING", "RUNNING", "EXECUTION_DONE",
          "ARTIFACT_VERIFIED", "INTEGRATION_VERIFIED", "FAILED", "BLOCKED",
          "UNKNOWN_EXECUTION", "CANCEL_REQUESTED", "CANCELLED"}
PREPARED = {"READY", "DISPATCHING", "RUNNING", "EXECUTION_DONE",
            "ARTIFACT_VERIFIED", "INTEGRATION_VERIFIED"}
OUTCOMES = {"PASS", "FAILED", "BLOCKED", "NOT_TESTED", "NOT_APPLICABLE"}


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def validate(record):
    """Return errors; assertions describe records, not independently observed facts."""
    errors = []
    if not isinstance(record, dict):
        return ["record must be an object"]

    def get(path):
        value = record
        for key in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

    def is_nonempty_text(value):
        return isinstance(value, str) and bool(value.strip()) and value.strip() != "UNKNOWN"

    def require(path):
        value = get(path)
        valid = bool(value) if isinstance(value, list) else is_nonempty_text(value)
        if not valid:
            errors.append(f"{path}: required for {state}")

    def safe_component(value):
        return (isinstance(value, str) and bool(value) and value == value.strip()
                and value not in (".", "..") and not any(c in value for c in "/\\:")
                and not any(unicodedata.category(c) == "Cc" for c in value))

    state = get("status")
    version = record.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        errors.append("schema_version: supported integer versions are 1 and 2; omitted means legacy 1")
    if not isinstance(state, str):
        return ["status: must be a string"]
    if state not in STATES:
        errors.append("status: unsupported lifecycle state")
    for key in ("executor", "baseline", "limits", "fallback", "observation", "outcomes", "result"):
        if not isinstance(get(key), dict):
            errors.append(f"{key}: must be an object")
    for path in ("dependencies", "writable_paths", "actual_grants", "inputs",
                 "deliverables", "acceptance", "evidence", "unresolved",
                 "fallback.ordered_routes", "fallback.resolved_routes", "result.files",
                 "result.checks"):
        if not isinstance(get(path), list):
            errors.append(f"{path}: must be an array")
    for key in ("execution", "artifacts", "integration"):
        if not isinstance(get(f"outcomes.{key}"), str) or get(f"outcomes.{key}") not in OUTCOMES:
            errors.append(f"outcomes.{key}: unsupported outcome")
    policy = get("fallback.policy")
    if policy not in ("inherit_project_default", "explicit_order", "exclusive"):
        errors.append("fallback.policy: unsupported policy")
    # Do not continue into iteration/semantic checks after schema type errors.
    if errors:
        return errors
    for field in ("task_id", "attempt_id"):
        value = get(field)
        if value is not None and not safe_component(value):
            errors.append(f"{field}: must be a safe single directory component")
    for path in ("inputs", "writable_paths", "actual_grants", "deliverables", "evidence", "result.files"):
        for index, item in enumerate(get(path)):
            if not is_nonempty_text(item):
                errors.append(f"{path}[{index}]: needs nonempty text")
    seen_files = set()
    for item in get("result.files"):
        if not isinstance(item, str):
            continue
        parts = item.split("/")
        normalized = "/".join(p for p in parts if p not in ("", "."))
        if (item.startswith("/") or item.endswith("/") or "\\" in item or re.match(r"^[A-Za-z]:", item)
                or ".." in parts or not normalized
                or any(unicodedata.category(c) == "Cc" for c in item)):
            errors.append("result.files: paths must be safe relative artifact paths")
        elif normalized in seen_files:
            errors.append("result.files: duplicate normalized artifact path")
        seen_files.add(normalized)
    # A file cannot also be the parent directory of another declared file.
    # Check normalized paths in both input orders.
    for name in seen_files:
        parts = name.split("/")
        if any("/".join(parts[:i]) in seen_files for i in range(1, len(parts))):
            errors.append("result.files: file path conflicts with a parent file")
    rounds = get("limits.same_issue_repair_rounds")
    if type(rounds) is not int or not 0 <= rounds <= 2:
        errors.append("limits.same_issue_repair_rounds: must be an integer from 0 to 2")
    for i, check in enumerate(get("result.checks")):
        if not isinstance(check, dict):
            errors.append(f"result.checks[{i}]: must be an object")
            continue
        for key in ("check_id", "candidate_identity", "evidence"):
            if not isinstance(check.get(key), str) or not check[key].strip() or check[key].strip() == "UNKNOWN":
                errors.append(f"result.checks[{i}].{key}: needs nonempty text")
        if not isinstance(check.get("result"), str) or check["result"] not in OUTCOMES:
            errors.append(f"result.checks[{i}].result: unsupported outcome")
        if check.get("stage", "artifacts") not in ("artifacts", "integration"):
            errors.append(f"result.checks[{i}].stage: unsupported stage")
    claims_pass = any(get(f"outcomes.{k}") == "PASS" for k in ("execution", "artifacts", "integration"))
    if state != "INTEGRATION_VERIFIED" and get("outcomes.integration") == "PASS":
        errors.append(f"{state}: full integration success must retain INTEGRATION_VERIFIED; record later cancellation separately")
    if state in {"CANCEL_REQUESTED", "CANCELLED"} and get("outcomes.execution") == "PASS":
        errors.append(f"{state}: a terminated successful attempt is EXECUTION_DONE or later, not cancelled")
    if state in {"DRAFT", "READY", "DISPATCHING", "RUNNING"} and claims_pass:
        errors.append(f"{state}: no completed PASS outcomes for this attempt")
    if state in PREPARED or claims_pass:
        for path in ("task_id", "attempt_id", "owner", "task_kind", "goal", "workspace",
                     "executor.software", "executor.transport", "executor.skill_mode",
                     "baseline.source_identity", "baseline.existing_user_changes",
                     "baseline.contract_version", "baseline.design_version", "actual_grants",
                     "deliverables", "result_location", "acceptance", "limits.task_deadline",
                     "limits.observation_wait", "fallback.resolved_routes",
                     "observation.submit_method", "observation.status_method",
                     "observation.collect_method"):
            require(path)
        if get("executor.skill_mode") not in ("read_apply", "native_skill", "task_instructions", "not_applicable"):
            errors.append("executor.skill_mode: unsupported mode")
        if get("task_kind") not in ("design", "frontend", "backend", "analysis", "verification", "other"):
            errors.append("task_kind: unsupported kind")
        routes = get("fallback.resolved_routes")
        selected = {"software": get("executor.software"), "transport": get("executor.transport")}
        def route_id(route):
            if (not isinstance(route, dict) or not is_nonempty_text(route.get("software"))
                    or not is_nonempty_text(route.get("transport"))):
                return None
            return (route["software"], route["transport"])
        if isinstance(routes, list):
            identities = [route_id(r) for r in routes]
            ordered = [route_id(r) for r in get("fallback.ordered_routes")]
            if None in identities or None in ordered:
                errors.append("fallback.resolved_routes: each route needs software and transport")
            if len(identities) != len(set(identities)):
                errors.append("fallback.resolved_routes: duplicate route identity")
            if len(ordered) != len(set(ordered)):
                errors.append("fallback.ordered_routes: duplicate route identity")
            if route_id(selected) not in identities:
                errors.append("selected executor must occur in resolved_routes")
            if policy == "exclusive" and identities != [route_id(selected)]:
                errors.append("exclusive policy permits exactly the selected route")
            if policy == "explicit_order" and identities != ordered:
                errors.append("explicit_order must preserve authorized ordered_routes; record skips separately")
        check_ids = []
        for i, item in enumerate(get("acceptance") or []):
            if not isinstance(item, dict) or any(not is_nonempty_text(item.get(k)) for k in
                    ("check_id", "requirement", "method", "verifier", "required_evidence")):
                errors.append(f"acceptance[{i}]: needs check_id, requirement, method, verifier, required_evidence")
            elif item["check_id"] in check_ids:
                errors.append(f"acceptance[{i}]: check_id must be a unique string")
            else:
                check_ids.append(item["check_id"])
            if isinstance(item, dict) and (
                    (version == 2 and "stage" not in item)
                    or ("stage" in item and item["stage"] not in ("artifacts", "integration"))):
                errors.append(f"acceptance[{i}].stage: requires artifacts or integration (mandatory in version 2)")
        for i, item in enumerate(get("dependencies") or []):
            if not isinstance(item, dict) or any(not is_nonempty_text(item.get(k)) for k in
                    ("task_id", "required_artifact", "required_state", "observed_state", "evidence")):
                errors.append(f"dependencies[{i}]: missing prerequisite identity/state/evidence")
            elif item["required_state"] not in ("EXECUTION_DONE", "ARTIFACT_VERIFIED", "INTEGRATION_VERIFIED"):
                errors.append(f"dependencies[{i}]: unsupported required_state")
            else:
                order = ["EXECUTION_DONE", "ARTIFACT_VERIFIED", "INTEGRATION_VERIFIED"]
                if item["observed_state"] not in order or order.index(item["observed_state"]) < order.index(item["required_state"]):
                    errors.append(f"dependencies[{i}]: prerequisite not satisfied")
    if state in {"BLOCKED", "UNKNOWN_EXECUTION"}:
        for path in ("observation.blocker", "next_action"):
            require(path)
    if state == "UNKNOWN_EXECUTION" and any(get(f"outcomes.{k}") == "PASS" for k in ("execution", "artifacts", "integration")):
        errors.append("unknown execution cannot claim PASS for this attempt")
    for outcome, required in (("artifacts", "execution"), ("integration", "artifacts")):
        if get(f"outcomes.{outcome}") == "PASS" and get(f"outcomes.{required}") != "PASS":
            errors.append(f"{outcome} PASS requires {required} PASS")
    levels = {"EXECUTION_DONE": "execution", "ARTIFACT_VERIFIED": "artifacts", "INTEGRATION_VERIFIED": "integration"}
    if state in levels and get("outcomes." + levels[state]) != "PASS":
        errors.append(f"{state} requires matching PASS outcome")
    if get("outcomes.execution") == "PASS":
        for path in ("evidence", "observation.observed_at"):
            require(path)
    if get("outcomes.artifacts") == "PASS":
        for path in ("result.candidate_identity", "result.files", "result.checks"):
            require(path)
        if get("result.scope_review") != "PASS":
            errors.append("artifact PASS requires scope_review PASS")
        latest = {}
        for check in get("result.checks"):
            if (isinstance(check, dict) and is_nonempty_text(check.get("check_id"))
                    and check.get("stage", "artifacts") == "artifacts"
                    and check.get("candidate_identity") == get("result.candidate_identity")):
                latest[check["check_id"]] = check
        if not any(check.get("result") == "PASS" for check in latest.values()):
            errors.append("artifact PASS requires a latest passing check bound to the current candidate")
        for check_id, check in latest.items():
            if check.get("result") not in ("PASS", "NOT_APPLICABLE"):
                errors.append(f"artifact check {check_id}: latest candidate-bound check is unresolved or failed")
        for item in get("acceptance"):
            if (isinstance(item, dict) and item.get("stage") == "artifacts"
                    and is_nonempty_text(item.get("check_id"))):
                check = latest.get(item.get("check_id"))
                if not check or check.get("result") != "PASS":
                    errors.append(f"acceptance {item.get('check_id')}: artifact requirement must PASS on current candidate")
    if get("outcomes.integration") == "PASS":
        if record.get("schema_version", 1) == 2 and not any(
                isinstance(item, dict) and item.get("stage") == "integration"
                for item in (get("acceptance") or [])):
            errors.append("v2 integration PASS requires declared integration acceptance")
        if get("result.integration_decision") != "PASS":
            errors.append("integration PASS requires integration_decision PASS")
        checks = get("result.checks")
        checks = checks if isinstance(checks, list) else []
        latest_integration = {}
        for check in checks:
            if (isinstance(check, dict) and is_nonempty_text(check.get("check_id"))
                    and check.get("stage") == "integration"
                    and check.get("candidate_identity") == get("result.candidate_identity")):
                latest_integration[check["check_id"]] = check
        for check_id, check in latest_integration.items():
            if check.get("result") not in ("PASS", "NOT_APPLICABLE"):
                errors.append(f"integration check {check_id}: latest candidate-bound check is unresolved or failed")
        for item in get("acceptance") or []:
            if isinstance(item, dict):
                matching = [c for c in checks if isinstance(c, dict)
                            and c.get("check_id") == item.get("check_id")
                            and c.get("candidate_identity") == get("result.candidate_identity")
                            and ("stage" not in item or c.get("stage", "artifacts") == item["stage"])]
                if not matching or matching[-1].get("result") != "PASS" or not matching[-1].get("evidence"):
                    errors.append(f"acceptance {item.get('check_id')}: latest candidate-bound check must PASS with evidence")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON record; YAML accepted only if PyYAML is already available")
    args = parser.parse_args()
    try:
        text = args.record.read_text(encoding="utf-8-sig")
        if args.record.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError:
                raise ValueError("YAML requires existing PyYAML; use the JSON template without installing dependencies")

            class UniqueSafeLoader(yaml.SafeLoader):
                def construct_mapping(self, node, deep=False):
                    if not isinstance(node, yaml.MappingNode):
                        raise ValueError("YAML mapping must contain key/value pairs")
                    seen = set()
                    # Inspect explicit keys before SafeLoader expands merge
                    # keys; a standard merge override remains valid YAML.
                    for key_node, _ in node.value:
                        key = ("<<" if key_node.tag == "tag:yaml.org,2002:merge"
                               else self.construct_object(key_node, deep=deep))
                        try:
                            if key in seen:
                                raise ValueError(f"duplicate YAML field: {key}")
                            seen.add(key)
                        except TypeError as exc:
                            raise ValueError("YAML mapping keys must be hashable") from exc
                    return super().construct_mapping(node, deep=deep)

            try:
                record = yaml.load(text, Loader=UniqueSafeLoader)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML: {exc}") from exc
        else:
            record = json.loads(text, object_pairs_hook=unique_json_object)
        errors = validate(record)
    except (OSError, ValueError) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"result": "INVALID" if errors else "VALID_RECORD", "errors": errors,
                      "scope": "Structural record checks only; no dispatch, authorization or runtime verification"}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
