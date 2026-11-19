"""Synthetic record tests; never evidence of desktop engineering capability."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_task import validate


def template():
    return json.loads((Path(__file__).resolve().parents[1] / "assets/task-template.json").read_text())


def ready():
    r = template()
    r.update(task_id="synthetic-1", attempt_id="attempt-1", task_kind="frontend",
             goal="Synthetic form implementation", workspace="/synthetic/workspace",
             actual_grants=["synthetic workspace read/write (fixture only)"],
             deliverables=["form source"], result_location="/synthetic/result", status="READY")
    r["executor"].update(software="gemini-desktop", transport="desktop", skill_mode="task_instructions")
    r["baseline"] = dict(source_identity="fixture-hash", existing_user_changes="none in fixture",
                         contract_version="fixture-contract-1", design_version="not applicable: behavior-only fixture")
    r["limits"].update(task_deadline="synthetic deadline", observation_wait="bounded tool wait")
    r["fallback"].update(policy="exclusive", resolved_routes=[dict(software="gemini-desktop", transport="desktop")])
    r["observation"].update(submit_method="fixture-submit", status_method="fixture-status", collect_method="fixture-collect")
    r["acceptance"] = [dict(check_id="form-submit", requirement="submits form", method="fixture test",
                            verifier="main", required_evidence="candidate-bound test output", stage="artifacts")]
    return r


def verified():
    r = ready()
    r["status"] = "INTEGRATION_VERIFIED"
    r["outcomes"] = dict(execution="PASS", artifacts="PASS", integration="PASS")
    r["evidence"] = ["synthetic terminal evidence"]
    r["observation"]["observed_at"] = "synthetic-time"
    r["result"].update(candidate_identity="candidate-1", files=["form.py"],
        scope_review="PASS", integration_decision="PASS", checks=[dict(
            check_id="form-submit", result="PASS", evidence="fixture-output",
            candidate_identity="candidate-1")])
    r["acceptance"].append(dict(check_id="business-flow", requirement="integrated submit",
        method="fixture integration", verifier="main", required_evidence="fixture output", stage="integration"))
    r["result"]["checks"].append(dict(check_id="business-flow", stage="integration", result="PASS",
        evidence="fixture integration output", candidate_identity="candidate-1"))
    return r


class RecordValidationTests(unittest.TestCase):
    def test_integration_pass_requires_verified_lifecycle(self):
        for state in ('BLOCKED', 'EXECUTION_DONE', 'ARTIFACT_VERIFIED', 'RUNNING'):
            record = verified()
            record['status'] = state
            record['observation']['blocker'] = 'Required login flow fails'
            record['next_action'] = 'Fix required login failure'
            with self.subTest(state=state):
                self.assertTrue(validate(record))

    def test_artifact_file_manifest_rejects_directory_and_parent_collisions(self):
        for files in (["src", "src/app.py"], ["src/app.py", "src"],
                      ["src/./app.py", "src/app.py/assets.json"], ["src/"]):
            with self.subTest(files=files):
                r = verified()
                r["result"]["files"] = files
                self.assertTrue(validate(r))
        r = verified()
        r["result"]["files"] = ["src/app.py", "src/application.py", "assets/icon.png"]
        self.assertEqual(validate(r), [])

    def test_local_read_apply_is_valid_without_claiming_native_loading(self):
        r = ready()
        r['executor'].update(software='codex', transport='native', skill_mode='read_apply')
        r['fallback']['resolved_routes'] = [dict(software='codex', transport='native')]
        self.assertEqual(validate(r), [])
        r['executor']['skill_mode'] = 'loaded_somehow'
        self.assertTrue(validate(r))

    def test_inputs_and_draft_identifiers_reject_invalid_values(self):
        for value in (None, False, {}, [], 0, "UNKNOWN", " "):
            r = ready(); r["inputs"] = [value]
            with self.subTest(input=value): self.assertTrue(validate(r))
        r = ready(); r["inputs"] = ["source.py sha256:fixture; relative to workspace"]
        self.assertEqual(validate(r), [])
        for field in ("task_id", "attempt_id"):
            for value in (False, 0, [], {}, ""):
                r = template(); r[field] = value
                with self.subTest(field=field, value=value): self.assertTrue(validate(r))

    def test_route_identity_ignores_metadata_but_not_order_or_duplicates(self):
        r = ready(); r["fallback"]["resolved_routes"][0]["reason"] = "user choice"
        self.assertEqual(validate(r), [])
        r["fallback"]["policy"] = "explicit_order"
        r["fallback"]["ordered_routes"] = [dict(software="gemini-desktop", transport="desktop")]
        self.assertEqual(validate(r), [])
        r["fallback"]["resolved_routes"].append(dict(software="gemini-desktop", transport="desktop"))
        self.assertTrue(validate(r))
        r = ready(); r["fallback"].update(policy="explicit_order", ordered_routes=[False])
        self.assertTrue(validate(r))

    def test_terminal_failure_and_cancellation_cannot_claim_full_success(self):
        for state in ("FAILED", "CANCEL_REQUESTED", "CANCELLED"):
            r = verified(); r["status"] = state
            with self.subTest(state=state): self.assertTrue(validate(r))
        r = verified(); r["status"] = "FAILED"; r["outcomes"]["integration"] = "FAILED"
        self.assertEqual(validate(r), [])  # Earlier completed layers remain valid.
        r = ready(); r["status"] = "CANCELLED"
        self.assertEqual(validate(r), [])

    def test_versioned_acceptance_covers_each_required_layer(self):
        r = verified(); r["schema_version"] = 2
        r["acceptance"][0]["stage"] = "artifacts"
        self.assertEqual(validate(r), [])
        r["status"] = "ARTIFACT_VERIFIED"; r["outcomes"]["integration"] = "NOT_TESTED"
        r["result"]["checks"][0]["result"] = "NOT_APPLICABLE"
        r["result"]["checks"].append(dict(check_id="incidental", result="PASS",
            candidate_identity="candidate-1", evidence="fixture"))
        self.assertTrue(validate(r))
        r["acceptance"][0]["stage"] = "integration"
        self.assertEqual(validate(r), [])  # Deferred business acceptance is separate.
        r["status"] = "INTEGRATION_VERIFIED"; r["outcomes"]["integration"] = "PASS"
        r["result"]["checks"][0]["result"] = "PASS"
        self.assertTrue(validate(r))  # Artifact-stage PASS cannot satisfy integration-stage item.
        r["result"]["checks"][0]["stage"] = "integration"
        self.assertEqual(validate(r), [])

    def test_v2_integration_requires_declared_integration_acceptance(self):
        r = verified()
        r["acceptance"] = [a for a in r["acceptance"] if a["stage"] == "artifacts"]
        self.assertTrue(validate(r))
        r["status"] = "ARTIFACT_VERIFIED"; r["outcomes"]["integration"] = "NOT_TESTED"
        self.assertEqual(validate(r), [])

    def test_schema_versions_and_legacy_acceptance_are_explicit(self):
        r = verified(); r.pop("schema_version", None)
        del r["acceptance"][0]["stage"]
        self.assertEqual(validate(r), [])  # Existing v1 records retain semantics.
        r["acceptance"][0]["stage"] = "invalid"
        self.assertTrue(validate(r))
        for version in (None, False, "2", 0, 3, []):
            r = ready(); r["schema_version"] = version
            with self.subTest(version=version): self.assertTrue(validate(r))
        r = ready(); r["schema_version"] = 2
        del r["acceptance"][0]["stage"]
        self.assertTrue(validate(r))  # Version 2 requires explicit acceptance stage.

    def test_task_and_attempt_ids_cannot_escape_exchange_subdirectories(self):
        for field in ("task_id", "attempt_id"):
            for value in ("..", ".", "../other", "/tmp/task", "a/b", "a\\b", "x\x00y", "task\n", " task"):
                r = ready()
                r[field] = value
                with self.subTest(field=field, value=value):
                    self.assertTrue(validate(r))
        r = ready()
        r.update(task_id="中文-task.1", attempt_id="尝试-001")
        self.assertEqual(validate(r), [])

    def test_result_file_paths_are_relative_and_nonduplicated(self):
        for files in (["../source.py"], ["/tmp/out.py"], ["a/../../source.py"],
                      ["C:\\outside.py"], ["C:outside.py"], ["a\\b.py"], ["."],
                      ["a.py", "./a.py"], ["a/b.py", "a//b.py"], ["file\x00.py"]):
            r = verified()
            r["result"]["files"] = files
            with self.subTest(files=files):
                self.assertTrue(validate(r))
        r = verified()
        r["result"]["files"] = ["中文 space/form.py"]
        self.assertEqual(validate(r), [])

    def test_deferred_integration_checks_do_not_block_artifact_acceptance(self):
        r = verified()
        r["status"] = "ARTIFACT_VERIFIED"
        r["outcomes"]["integration"] = "NOT_TESTED"
        deferred = dict(check_id="real-service", candidate_identity="candidate-1",
                        stage="integration", result="NOT_TESTED", evidence="Real service test deferred")
        r["result"]["checks"].append(deferred)
        self.assertEqual(validate(r), [])
        r["status"] = "INTEGRATION_VERIFIED"
        r["outcomes"]["integration"] = "PASS"
        self.assertTrue(validate(r))
        deferred["result"] = "PASS"
        self.assertEqual(validate(r), [])
        r["result"]["checks"].append(dict(deferred, result="FAILED"))
        self.assertTrue(validate(r))
        r["result"]["checks"].append(dict(deferred, result="PASS"))
        self.assertEqual(validate(r), [])

    def test_invalid_check_stage_is_rejected(self):
        for stage in (None, [], "unknown", "", False):
            r = verified()
            r["result"]["checks"][0]["stage"] = stage
            with self.subTest(stage=stage):
                self.assertTrue(validate(r))

    def test_cli_malformed_yaml_mapping_returns_structured_error(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("Optional PyYAML is not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("!!map [1, 2]\n")
            result = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("validate_task.py")),
                                     str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout)["result"], "ERROR")
            self.assertEqual(result.stderr, "")

    def test_text_arrays_reject_placeholder_and_non_text_entries(self):
        for field in ("actual_grants", "deliverables", "writable_paths", "evidence", "result.files"):
            for value in (None, False, 0, {}, [], " ", "UNKNOWN"):
                r = verified()
                parent = r
                parts = field.split(".")
                for part in parts[:-1]:
                    parent = parent[part]
                parent[parts[-1]] = [value]
                with self.subTest(field=field, value=value):
                    self.assertTrue(validate(r))

    def test_repair_limit_is_an_integer_within_two_rounds(self):
        for bad in (None, True, "2", 2.0, -1, 3, [], {}):
            r = ready()
            r["limits"]["same_issue_repair_rounds"] = bad
            with self.subTest(value=bad):
                self.assertTrue(validate(r))
        for allowed in (0, 1, 2):
            r = ready()
            r["limits"]["same_issue_repair_rounds"] = allowed
            self.assertEqual(validate(r), [])

    def test_cli_reads_utf8_bom_and_rejects_duplicate_json_keys(self):
        script = Path(__file__).with_name("validate_task.py")
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "任务 record.json"
            cases = [(b"\xef\xbb\xbf" + json.dumps(template()).encode(), 0, "VALID_RECORD"),
                     (json.dumps(template()).replace('"status": "DRAFT"',
                         '"status": "RUNNING", "status": "DRAFT"').encode(), 2, "ERROR"),
                     (json.dumps(template()).replace('"same_issue_repair_rounds": 2',
                         '"same_issue_repair_rounds": 99, "same_issue_repair_rounds": 2').encode(),
                      2, "ERROR")]
            for content, code, expected in cases:
                record.write_bytes(content)
                result = subprocess.run([sys.executable, "-B", str(script), str(record)],
                                        capture_output=True, text=True)
                with self.subTest(content=content[:30], expected=expected):
                    self.assertEqual(result.returncode, code, result.stdout)
                    self.assertEqual(json.loads(result.stdout)["result"], expected)
                    self.assertEqual(record.read_bytes(), content)

    def test_yaml_duplicate_keys_are_rejected_when_yaml_is_available(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("Optional PyYAML is not installed")
        script = Path(__file__).with_name("validate_task.py")
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "task.yaml"
            valid = yaml.safe_dump(template(), allow_unicode=True)
            for text, expected in ((valid, 0),
                                   ("defaults: &defaults {status: RUNNING}\n<<: *defaults\n" + valid, 0),
                                   (valid + "status: RUNNING\n", 2),
                                   (valid.replace("same_issue_repair_rounds: 2",
                                       "same_issue_repair_rounds: 99\n  same_issue_repair_rounds: 2"), 2)):
                record.write_text(text, encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", str(script), str(record)],
                                        capture_output=True, text=True)
                with self.subTest(expected=expected):
                    self.assertEqual(result.returncode, expected, result.stdout)
                    self.assertEqual(record.read_text(), text)

    def test_nested_sections_must_be_objects_even_in_draft(self):
        for key in ("executor", "baseline", "limits", "observation", "result", "fallback", "outcomes"):
            r = template(); r[key] = []
            with self.subTest(key=key): self.assertTrue(validate(r))

    def test_required_text_cannot_be_boolean_number_or_whitespace(self):
        for key in ("task_id", "workspace", "goal"):
            for value in (True, 42, "   "):
                r = ready(); r[key] = value
                with self.subTest(key=key, value=value): self.assertTrue(validate(r))

    def test_artifact_checks_must_be_structured_and_candidate_bound(self):
        for value in (["fake-check"], [dict(check_id="form-submit", result="PASS")]):
            r = verified(); r["status"] = "ARTIFACT_VERIFIED"
            r["outcomes"]["integration"] = "NOT_TESTED"
            r["result"]["checks"] = value
            with self.subTest(value=value): self.assertTrue(validate(r))

    def test_latest_same_candidate_failure_invalidates_earlier_pass(self):
        r = verified()
        later = copy.deepcopy(r["result"]["checks"][0]); later["result"] = "FAILED"
        r["result"]["checks"].append(later)
        self.assertTrue(validate(r))
        r["result"]["checks"].append(copy.deepcopy(r["result"]["checks"][0]))
        self.assertEqual(validate(r), [])  # Earlier failures stay in ordered history.

    def test_artifact_pass_rejects_failed_or_unfinished_current_checks(self):
        for outcome in ("FAILED", "BLOCKED", "NOT_TESTED", "NOT_APPLICABLE"):
            r = verified()
            r["status"] = "ARTIFACT_VERIFIED"
            r["outcomes"]["integration"] = "NOT_TESTED"
            r["result"]["checks"][0]["result"] = outcome
            with self.subTest(outcome=outcome):
                self.assertTrue(validate(r))

    def test_artifact_checks_use_latest_per_check_and_current_candidate(self):
        r = verified()
        r["status"] = "ARTIFACT_VERIFIED"
        r["outcomes"]["integration"] = "NOT_TESTED"
        passed = copy.deepcopy(r["result"]["checks"][0])
        failed = dict(passed, result="FAILED")
        r["result"]["checks"].append(failed)
        self.assertTrue(validate(r))
        r["result"]["checks"].append(passed)
        self.assertEqual(validate(r), [])
        r["result"]["checks"].append(dict(failed, candidate_identity="old-candidate"))
        self.assertEqual(validate(r), [])
        r["result"]["checks"].append(dict(failed, check_id="build"))
        self.assertTrue(validate(r))
        r["result"]["checks"].append(dict(passed, check_id="build", result="NOT_APPLICABLE",
                                            evidence="No build step for this documentation-only candidate"))
        self.assertEqual(validate(r), [])

    def test_cli_exit_codes_json_and_read_only_input(self):
        script = Path(__file__).with_name("validate_task.py")
        cases = [(json.dumps(template()), 0, "VALID_RECORD"),
                 ('{"status": "READY"}', 1, "INVALID"),
                 ('{broken-json', 2, "ERROR")]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "record.json"
            for text, code, result in cases:
                p.write_text(text)
                completed = subprocess.run([sys.executable, "-B", str(script), str(p)],
                                           capture_output=True, text=True)
                with self.subTest(code=code):
                    self.assertEqual(completed.returncode, code)
                    self.assertEqual(json.loads(completed.stdout)["result"], result)
                    self.assertEqual(completed.stderr, "")
                    self.assertEqual(p.read_text(), text)

    def test_draft_is_record_not_dispatch_permission(self):
        self.assertEqual(validate(template()), [])
        r = template(); r["status"] = "READY"
        self.assertTrue(validate(r))

    def test_prepared_record_and_optional_cancel_resume(self):
        self.assertEqual(validate(ready()), [])

    def test_missing_grants_and_unsatisfied_dependency(self):
        r = ready(); r["actual_grants"] = []
        self.assertTrue(validate(r))
        r = ready(); r["dependencies"] = [dict(task_id="design", required_artifact="export",
            required_state="ARTIFACT_VERIFIED", observed_state="EXECUTION_DONE", evidence="fixture")]
        self.assertTrue(validate(r))

    def test_exclusive_and_ordered_routes(self):
        r = ready(); r["fallback"]["resolved_routes"].append(dict(software="codex", transport="native"))
        self.assertTrue(validate(r))
        r = ready(); r["fallback"]["policy"] = "explicit_order"
        self.assertTrue(validate(r))

    def test_unknown_execution_cannot_claim_success(self):
        r = ready(); r.update(status="UNKNOWN_EXECUTION", next_action="reconcile original attempt")
        r["observation"]["blocker"] = "submission receipt unavailable"
        self.assertEqual(validate(r), [])
        r["outcomes"]["execution"] = "PASS"
        self.assertTrue(validate(r))

    def test_integration_needs_matching_candidate_evidence(self):
        r = ready(); r.pop("schema_version"); r["status"] = "INTEGRATION_VERIFIED"
        r["outcomes"] = dict(execution="PASS", artifacts="PASS", integration="PASS")
        self.assertTrue(validate(r))
        r["evidence"] = ["synthetic terminal evidence"]
        r["observation"]["observed_at"] = "synthetic-time"
        r["result"].update(candidate_identity="candidate-1", files=["form.py"], scope_review="PASS",
            integration_decision="PASS", checks=[dict(check_id="form-submit", result="PASS",
                evidence="fixture-output", candidate_identity="candidate-1")])
        self.assertEqual(validate(r), [])
        r["result"]["checks"][0]["candidate_identity"] = "old-candidate"
        self.assertTrue(validate(r))

    def test_bad_types_are_errors_not_exceptions(self):
        for path in ("status", "fallback.policy", "executor.skill_mode", "task_kind",
                     "outcomes.execution", "acceptance", "dependencies"):
            for bad in (None, [], {}, 123):
                if path == "dependencies" and bad == []:
                    continue  # Independent tasks legitimately have no dependencies.
                r = ready(); parent = r; parts = path.split(".")
                for key in parts[:-1]: parent = parent[key]
                parent[parts[-1]] = copy.deepcopy(bad)
                with self.subTest(path=path, value=bad):
                    self.assertTrue(validate(r))

    def test_unprepared_records_cannot_claim_integration(self):
        for state in ("DRAFT", "FAILED", "READY", "RUNNING"):
            r = template(); r["status"] = state
            r["outcomes"] = dict(execution="PASS", artifacts="PASS", integration="PASS")
            r["evidence"] = ["fixture"]; r["observation"]["observed_at"] = "fixture"
            r["result"].update(candidate_identity="fixture", files=["fixture"], checks=["fixture"],
                               scope_review="PASS", integration_decision="PASS")
            with self.subTest(state=state): self.assertTrue(validate(r))

    def test_acceptance_ids_are_unique(self):
        r = ready(); r["acceptance"].append(copy.deepcopy(r["acceptance"][0]))
        self.assertTrue(validate(r))

    def test_nested_entry_textual_fields_reject_non_text_whitespace_and_unknown(self):
        for bad in (True, 42, "   ", "UNKNOWN"):
            for field in ("check_id", "requirement", "method", "verifier", "required_evidence"):
                r = ready()
                r["acceptance"][0][field] = bad
                with self.subTest(section="acceptance", field=field, bad=bad):
                    self.assertTrue(validate(r))
            for field in ("task_id", "required_artifact", "evidence"):
                r = ready()
                r["dependencies"] = [dict(task_id="design", required_artifact="export",
                    required_state="ARTIFACT_VERIFIED", observed_state="ARTIFACT_VERIFIED",
                    evidence="fixture")]
                r["dependencies"][0][field] = bad
                with self.subTest(section="dependencies", field=field, bad=bad):
                    self.assertTrue(validate(r))
            for field in ("software", "transport"):
                r = ready()
                r["fallback"]["policy"] = "inherit_project_default"
                extra = dict(software="codex", transport="native")
                extra[field] = bad
                r["fallback"]["resolved_routes"].append(extra)
                with self.subTest(section="resolved_routes", field=field, bad=bad):
                    self.assertTrue(validate(r))


if __name__ == "__main__":
    unittest.main()
