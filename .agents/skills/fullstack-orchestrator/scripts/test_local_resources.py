"""Real-process resource exclusion and recovery invariants; all state is temporary."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).with_name('local_resources.py')
spec = importlib.util.spec_from_file_location('local_resources', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LocalResourcesTests(unittest.TestCase):
    def test_ambiguous_state_rejected_without_mutation(self):
        code, result = self.acquire(0, '--development')
        self.assertEqual(code, 0)
        path = self.state / 'state.json'
        original = path.read_text()
        cases = [original.rstrip()[:-1] + ',"grants":[]}',
                 original.replace('"created_at":', '"created_at":0,"created_at":', 1)]
        import re
        for value in ('NaN', 'Infinity', '1e999', str(10**400)):
            cases.append(re.sub(r'"created_at": [0-9.]+', '"created_at": '+value, original, count=1))
        for content in cases:
            with self.subTest(content=content[-80:]):
                path.write_text(content)
                self.assertNotEqual(self.cli('status')[0], 0)
                self.assertNotEqual(self.acquire(1, '--development')[0], 0)
                self.assertNotEqual(self.cli('configure', '--development-limit', '5', '--confirmed', '--evidence', 'fixture')[0], 0)
                self.assertNotEqual(self.release(result['grant']['token'])[0], 0)
                self.assertEqual(path.read_text(), content)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.projects = [self.root / f'project-{n}' for n in range(3)]
        for project in self.projects:
            project.mkdir()

    def cli(self, *args, retry=False):
        for _ in range(100):
            process = subprocess.run([sys.executable, str(SCRIPT), '--state-dir', str(self.state), *args], text=True, capture_output=True)
            self.assertEqual(process.stderr, '')
            result = json.loads(process.stdout)
            if retry and result.get('reason') == 'coordination_transaction_busy_retry_without_dispatch':
                time.sleep(.01)
                continue
            return process.returncode, result
        self.fail('transaction remained busy')

    def acquire(self, index=0, *resources, **kwargs):
        args = ['acquire', '--project-root', str(kwargs.get('project', self.projects[index])), '--coordinator', kwargs.get('coordinator', f'main-{index}'), '--task', kwargs.get('task', 'task'), '--attempt', kwargs.get('attempt', 'attempt-1')]
        if 'operation' in kwargs:
            args += ['--operation', kwargs['operation']]
        return self.cli(*args, *resources, retry=True)

    def release(self, token, evidence='actual completion observed'):
        return self.cli('release', '--token=' + token, '--confirmed', '--evidence', evidence, retry=True)

    def test_status_does_not_initialize(self):
        self.assertEqual(self.cli('status')[1]['grants'], [])
        self.assertFalse(self.state.exists())

    def test_three_processes_two_development_grants(self):
        self.configure(2)
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            results = list(pool.map(lambda n: self.acquire(n, '--development'), range(3)))
        self.assertEqual(sum(code == 0 for code, _ in results), 2)
        self.assertEqual(sum(code == 2 for code, _ in results), 1)
        self.assertEqual(len(self.cli('status')[1]['grants']), 2)

    def test_three_processes_only_one_gui(self):
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            results = list(pool.map(lambda n: self.acquire(n, '--gui'), range(3)))
        self.assertEqual(sum(code == 0 for code, _ in results), 1)
        self.assertEqual(sum(code == 2 for code, _ in results), 2)

    def test_process_exit_does_not_release_and_status_redacts_tokens(self):
        _, result = self.acquire(0, '--gui')
        status = self.cli('status')[1]
        self.assertNotIn(result['grant']['token'], json.dumps(status))
        self.assertEqual(self.acquire(1, '--gui')[0], 2)
        self.assertEqual(self.cli('check', '--token=' + result['grant']['token'])[1]['status'], 'OWNED')

    def test_atomic_bundle_no_capacity_leak(self):
        self.acquire(0, '--gui')
        code, waiting = self.acquire(1, '--gui', '--development')
        self.assertEqual(code, 2)
        self.assertEqual(len(self.cli('status')[1]['grants']), 1)
        self.assertEqual(self.cli('cancel-wait', '--token=' + waiting['wait']['token'], '--confirmed', '--evidence', 'Changed requested bundle before dispatch')[0], 0)
        self.assertEqual(self.acquire(1, '--development')[0], 0)
        self.assertEqual(self.acquire(2, '--development')[0], 0)

    def test_alias_workspace_conflicts(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.projects[0], target_is_directory=True)
        self.acquire(0, '--write-workspace', str(self.projects[0]))
        self.assertEqual(self.acquire(1, '--write-workspace', str(alias))[0], 2)

    def test_same_identity_idempotence_and_bundle_change_rejected(self):
        _, first = self.acquire(0, '--development')
        _, again = self.acquire(0, '--development')
        self.assertEqual(first['grant'], again['grant'])
        self.assertTrue(again['idempotent'])
        self.assertEqual(self.acquire(0, '--gui')[0], 1)

    def test_active_task_blocks_new_attempt_and_other_coordinator(self):
        self.acquire(0, '--development')
        self.assertEqual(self.acquire(0, '--gui', attempt='attempt-2')[0], 2)
        self.assertEqual(self.acquire(0, '--gui', coordinator='different')[0], 2)
        self.assertEqual(self.acquire(0, '--gui', operation='submit')[0], 0)

    def test_release_requires_token_confirmation_and_evidence(self):
        _, first = self.acquire(0, '--gui')
        token = first['grant']['token']
        self.assertEqual(self.release('wrong')[0], 1)
        self.assertEqual(self.cli('release', '--token=' + token, '--evidence', 'done')[0], 1)
        self.assertEqual(self.release(token, ' ')[0], 1)
        self.assertEqual(self.release(token)[0], 0)
        self.assertEqual(self.cli('check', '--token=' + token)[0], 1)
        _, second = self.acquire(1, '--gui')
        self.assertGreater(second['grant']['generation'], first['grant']['generation'])
        self.assertNotEqual(token, second['grant']['token'])

    def test_corrupt_state_no_reset(self):
        self.acquire(0, '--gui')
        path = self.state / 'state.json'
        path.write_text('{bad')
        self.assertEqual(self.acquire(1, '--gui')[0], 1)
        self.assertEqual(path.read_text(), '{bad')

    def test_linked_state_and_nonprivate_directory_refused(self):
        self.state.mkdir(mode=0o700)
        target = self.root / 'outside'
        target.write_text('{}')
        (self.state / 'state.json').symlink_to(target)
        self.assertEqual(self.acquire(0, '--gui')[0], 1)
        self.assertEqual(target.read_text(), '{}')
        (self.state / 'state.json').unlink()
        os.chmod(self.state, 0o755)
        self.assertEqual(self.acquire(0, '--gui')[0], 1)

    def test_lock_busy_is_bounded_and_lock_file_stable(self):
        import fcntl
        _, first = self.acquire(0, '--gui')
        lock = self.state / 'transaction.lock'
        inode = lock.stat().st_ino
        with lock.open('r+') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            code, response = self.cli('status')
            self.assertEqual(code, 2)
            self.assertEqual(response['reason'], 'coordination_transaction_busy_retry_without_dispatch')
        self.release(first['grant']['token'])
        self.assertEqual(lock.stat().st_ino, inode)

    def test_malformed_resource_state_rejected(self):
        self.acquire(0, '--development')
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state['grants'].append(dict(state['grants'][0]))
        path.write_text(json.dumps(state))
        self.assertEqual(self.cli('status')[0], 1)

    def test_deleted_state_and_linked_lock_fail_closed(self):
        self.acquire(0, '--gui')
        (self.state / 'state.json').unlink()
        self.assertEqual(self.acquire(1, '--gui')[0], 1)
        (self.state / 'transaction.lock').unlink()
        (self.state / 'transaction.lock').symlink_to(self.root / 'missing')
        self.assertEqual(self.cli('status')[0], 1)

    def test_missing_lock_with_existing_state_never_recreated(self):
        import fcntl
        self.acquire(0, '--gui')
        lock = self.state / 'transaction.lock'
        with lock.open('r+') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            lock.rename(self.state / 'old-lock')
            self.assertEqual(self.acquire(1, '--development')[0], 1)
            self.assertEqual(self.cli('status')[0], 1)
            self.assertFalse(lock.exists())

    def test_workspace_ancestor_descendant_both_orders_and_siblings(self):
        child = self.projects[0] / 'child'
        child.mkdir()
        sibling = self.projects[0] / 'sibling'
        sibling.mkdir()
        code, first = self.acquire(0, '--write-workspace', str(self.projects[0]))
        self.assertEqual(code, 0, first)
        self.assertEqual(self.acquire(1, '--write-workspace', str(child))[0], 2)
        released = self.release(first['grant']['token'])
        self.assertEqual(released[0], 0, released)
        code, second = self.acquire(1, '--write-workspace', str(child))
        self.assertEqual(code, 0, second)
        self.assertEqual(self.acquire(0, '--write-workspace', str(self.projects[0]))[0], 2)
        self.assertEqual(self.acquire(2, '--write-workspace', str(sibling))[0], 0)

    def test_generated_tokens_are_safe_separate_arguments(self):
        from unittest.mock import patch
        with patch.object(module.secrets, 'token_urlsafe', side_effect=['-leading-grant', '-leading-wait']):
            granted = module.run(module.parser().parse_args([
                '--state-dir', str(self.state), 'acquire', '--project-root', str(self.projects[0]),
                '--coordinator', 'main', '--task', 't', '--attempt', 'a', '--gui']))
            waiting = module.run(module.parser().parse_args([
                '--state-dir', str(self.state), 'acquire', '--project-root', str(self.projects[1]),
                '--coordinator', 'other', '--task', 't', '--attempt', 'a', '--gui']))
        token = granted['grant']['token']
        self.assertEqual(self.cli('check', '--token', token)[0], 0)
        self.assertEqual(self.cli('cancel-wait', '--token', waiting['wait']['token'],
                                  '--confirmed', '--evidence', 'No dispatch')[0], 0)
        self.assertEqual(self.release(token)[0], 0)

    def test_legacy_dash_tokens_supported_with_equals(self):
        granted = self.acquire(0, '--gui')[1]['grant']
        self.acquire(1, '--gui')
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state['grants'][0]['token'] = '-legacy-grant'
        state['waiters'][0]['token'] = '-legacy-wait'
        path.write_text(json.dumps(state))
        self.assertEqual(self.cli('check', '--token=-legacy-grant')[0], 0)
        self.assertEqual(self.cli('cancel-wait', '--token=-legacy-wait', '--confirmed',
                                  '--evidence', 'No dispatch')[0], 0)
        self.assertEqual(self.cli('release', '--token=-legacy-grant', '--confirmed',
                                  '--evidence', 'Execution stopped')[0], 0)

    def test_case_alias_workspace_and_project_capacity(self):
        actual = self.projects[0] / 'CaseProject'; actual.mkdir()
        alias = self.projects[0] / 'caseproject'
        if not alias.exists():
            self.skipTest('case-sensitive filesystem')
        self.assertTrue(actual.samefile(alias))
        first = self.acquire(0, '--write-workspace', str(actual), project=actual)
        self.assertEqual(first[0], 0, first)
        second = self.acquire(1, '--write-workspace', str(alias), project=alias, task='other')
        self.assertEqual(second[0], 2, second)
        self.assertEqual(self.release(first[1]['grant']['token'])[0], 0)
        self.acquire(0, '--development', project=actual, task='dev1')
        self.acquire(1, '--development', project=alias, task='dev2')
        third = self.acquire(2, '--development', project=actual, task='dev3')
        self.assertEqual(third[0], 2, third)
        self.assertIn('development:project_capacity', third[1]['resources'])

    def test_legacy_case_workspace_alias_conflicts(self):
        actual = self.projects[0] / 'CaseProject'; actual.mkdir()
        alias = self.projects[0] / 'caseproject'
        if not alias.exists():
            self.skipTest('case-sensitive filesystem')
        self.acquire(0, '--write-workspace', str(actual), project=actual)
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state['grants'][0]['project_root'] = str(alias.resolve())
        state['grants'][0]['resources'] = ['workspace:' + str(alias.resolve())]
        path.write_text(json.dumps(state))
        result = self.acquire(1, '--write-workspace', str(actual / '..'), task='other')
        self.assertEqual(result[0], 2, result)

    def test_missing_legacy_child_keeps_ancestor_lock(self):
        actual = self.projects[0] / 'CaseProject'; actual.mkdir()
        alias = self.projects[0] / 'caseproject'
        if not alias.exists():
            self.skipTest('case-sensitive filesystem')
        child = actual / 'child'; child.mkdir()
        self.acquire(0, '--write-workspace', str(child))
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state['grants'][0]['resources'] = ['workspace:' + str(alias.resolve() / 'child')]
        path.write_text(json.dumps(state))
        child.rmdir()
        result = self.acquire(1, '--write-workspace', str(actual))
        self.assertEqual(result[0], 2, result)

    def test_distinct_case_directories_when_supported(self):
        actual = self.projects[0] / 'CaseProject'; actual.mkdir()
        other = self.projects[0] / 'caseproject'
        if other.exists():
            self.skipTest('case-insensitive filesystem; distinct case directories unavailable')
        other.mkdir()
        self.assertEqual(self.acquire(0, '--write-workspace', str(actual))[0], 0)
        self.assertEqual(self.acquire(1, '--write-workspace', str(other))[0], 0)

    def test_firmlink_alias_conflicts_and_counts_project(self):
        temp = tempfile.TemporaryDirectory(dir=Path.home())
        self.addCleanup(temp.cleanup)
        project = Path(temp.name)
        alias = Path('/System/Volumes/Data') / str(project).lstrip('/')
        if not alias.is_dir() or not alias.samefile(project):
            self.skipTest('APFS firmlink alias unavailable')
        first = self.acquire(0, '--write-workspace', str(project), project=project)
        self.assertEqual(first[0], 0, first)
        self.assertEqual(self.acquire(1, '--write-workspace', str(alias), project=alias)[0], 2)
        self.assertTrue(module.same_project(str(alias), str(project)))
        self.assertTrue(module.resources_overlap('workspace:' + str(alias),
                                                 'workspace:' + str(project)))
        self.assertEqual(self.release(first[1]['grant']['token'])[0], 0)

    def test_legacy_project_replaced_by_file_remains_releasable(self):
        for ancestor in (False, True):
            with self.subTest(ancestor=ancestor):
                parent = self.projects[0] / ('ancestor' if ancestor else 'direct')
                parent.mkdir()
                target = parent / 'child' if ancestor else parent
                if ancestor:
                    target.mkdir()
                first = self.acquire(0, '--development', '--write-workspace', str(target), project=target)
                self.assertEqual(first[0], 0, first)
                if ancestor:
                    target.rmdir()
                parent.rmdir()
                parent.write_text('replacement')
                self.assertEqual(self.cli('status')[0], 0)
                blocked = self.acquire(1, '--write-workspace', str(self.projects[0]))
                self.assertEqual(blocked[0], 2, blocked)
                self.assertEqual(self.cli('cancel-wait', '--token=' + blocked[1]['wait']['token'],
                                          '--confirmed', '--evidence', 'No dispatch')[0], 0)
                self.assertEqual(self.acquire(2, '--development', project=target)[0], 1)
                self.assertEqual(self.release(first[1]['grant']['token'])[0], 0)

    def test_observed_path_does_not_suppress_permission_errors(self):
        from unittest.mock import patch
        with patch.object(Path, 'stat', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                module.observed_path(str(self.projects[0]))

    def test_reserved_resource_schema_rejects_invalid_values(self):
        import copy
        self.acquire(0, '--development')
        path = self.state / 'state.json'
        original = json.loads(path.read_text())
        invalid = ['development:257', 'gui:other', 'workspace:relative', 'workspace:/x/../y', 'exclusive:', 'exclusive: ', {'bad': 1}, ['nested'], 3]
        for key in invalid:
            with self.subTest(resource=key):
                candidate = copy.deepcopy(original)
                candidate['grants'][0]['resources'] = [key]
                path.write_text(json.dumps(candidate))
                self.assertEqual(self.cli('status')[0], 1)
        path.write_text(json.dumps(original))

    def test_state_rejects_conflicting_owner_attempt_overlap_and_generation(self):
        import copy
        _, first = self.acquire(0, '--write-workspace', str(self.projects[0]))
        self.acquire(1, '--development')
        path = self.state / 'state.json'
        original = json.loads(path.read_text())
        for corruption in ('owner', 'attempt', 'overlap', 'generation'):
            with self.subTest(corruption=corruption):
                candidate = copy.deepcopy(original)
                a, b = candidate['grants']
                if corruption in ('owner', 'attempt'):
                    b['project_root'], b['task'] = a['project_root'], a['task']
                    if corruption == 'attempt':
                        b['coordinator'] = a['coordinator']
                        b['attempt'] = 'other-attempt'
                elif corruption == 'overlap':
                    b['resources'] = ['workspace:' + str(self.projects[0].resolve() / 'child')]
                else:
                    b['generation'] = a['generation']
                path.write_text(json.dumps(candidate))
                self.assertEqual(self.cli('status')[0], 1)
        path.write_text(json.dumps(original))

    def test_json_error_for_invalid_cli(self):
        self.assertEqual(self.cli('acquire')[0], 1)

    def configure(self, limit):
        return self.cli('configure', '--development-limit', str(limit), '--confirmed', '--evidence', 'authorized temporary host policy', retry=True)

    def test_five_projects_four_developers_gui_stays_single(self):
        for n in range(3, 5):
            p = self.root / f'project-{n}'
            p.mkdir()
            self.projects.append(p)
        with concurrent.futures.ThreadPoolExecutor(5) as pool:
            results = list(pool.map(lambda n: self.acquire(n, '--development'), range(5)))
        self.assertEqual(sum(code == 0 for code, _ in results), 4)
        self.assertEqual(sum(code == 2 for code, _ in results), 1)
        self.assertEqual(self.acquire(0, '--gui', operation='gui')[0], 0)
        self.assertEqual(self.acquire(1, '--gui', operation='gui')[0], 2)

    def test_lower_capacity_preserves_active_and_blocks_even_free_low_slot(self):
        self.configure(4)
        grants = [self.acquire(n % 3, '--development', operation=f'worker-{n}')[1]['grant'] for n in range(4)]
        self.configure(2)
        self.assertEqual(len(self.cli('status')[1]['grants']), 4)
        for g in grants[:2]:
            self.release(g['token'])
        self.assertEqual(self.acquire(0, '--development', operation='new')[0], 2)
        self.release(grants[2]['token'])
        self.assertEqual(self.acquire(0, '--development', operation='new')[0], 0)

    def test_legacy_migration_preserves_token_and_old_validator_fails_closed(self):
        _, result = self.acquire(0, '--development')
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state.pop('development_limit'); state.pop('events'); state['schema'] = 1
        path.write_text(json.dumps(state))
        self.assertEqual(self.cli('status')[1]['development_limit'], 2)
        self.configure(4)
        self.assertEqual(self.cli('check', '--token=' + result['grant']['token'])[0], 0)
        legacy = SCRIPT.parents[4] / 'outputs/workflow-current-delivery/previous-project.31/.agents/skills/fullstack-orchestrator/scripts/local_resources.py'
        if legacy.exists():
            p = subprocess.run([sys.executable, str(legacy), '--state-dir', str(self.state), 'status'], capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)

    def test_configuration_authorization_bounds_and_event_privacy(self):
        self.assertEqual(self.cli('configure', '--development-limit', '4')[0], 1)
        for limit in (0, 257):
            self.assertEqual(self.configure(limit)[0], 1)
        self.configure(4)
        _, grant = self.acquire(0, '--development')
        self.release(grant['grant']['token'])
        status = self.cli('status')[1]
        self.assertEqual([e['action'] for e in status['events']], ['configure', 'acquire', 'release'])
        self.assertNotIn(grant['grant']['token'], json.dumps(status))
        state = json.loads((self.state / 'state.json').read_text())
        state['events'] = state['events'] * 34
        with self.assertRaises(module.CoordinationError):
            module.validate(state)

    def test_default_four_and_project_two_with_override(self):
        status = self.cli('status')[1]
        self.assertEqual((status['development_limit'], status['project_limit']), (4, 2))
        self.assertFalse(self.state.exists())
        first = self.acquire(0, '--development', operation='one')[1]['grant']
        self.acquire(0, '--development', operation='two')
        code, waiting = self.acquire(0, '--development', operation='three')
        self.assertEqual(code, 2)
        self.assertIn('development:project_capacity', waiting['resources'])
        self.assertEqual(self.cli('configure', '--project-root', str(self.projects[0]), '--project-limit', '3', '--confirmed', '--evidence', 'Explicit project exception')[0], 0)
        self.assertEqual(self.acquire(0, '--development', operation='three')[0], 0)
        self.assertEqual(self.acquire(1, '--development')[0], 0)
        self.assertEqual(self.acquire(2, '--development')[0], 2)
        self.assertEqual(self.cli('configure', '--project-root', str(self.projects[0]), '--project-limit', '1', '--confirmed', '--evidence', 'Lower without preemption')[0], 0)
        self.assertEqual(len(self.cli('status')[1]['grants']), 4)
        self.release(first['token'])
        self.assertEqual(self.acquire(0, '--development', operation='four')[0], 2)

    def test_wait_order_stable_and_unrelated_gui_can_proceed(self):
        self.configure(1)
        first = self.acquire(0, '--development')[1]['grant']
        older = self.acquire(1, '--development')[1]['wait']
        repeated = self.acquire(1, '--development')[1]['wait']
        self.assertEqual(older, repeated)
        newer = self.acquire(2, '--development')[1]['wait']
        self.release(first['token'])
        self.assertIn('queue:earlier_eligible_request', self.acquire(2, '--development')[1]['resources'])
        gui = self.acquire(0, '--gui', operation='gui')[1]['grant']
        self.assertEqual(self.acquire(1, '--development')[0], 0)
        status = self.cli('status')[1]
        self.assertNotIn(newer['token'], json.dumps(status))
        self.assertNotIn(gui['token'], json.dumps(status))
        self.assertEqual([w['ticket'] for w in status['waiters']], [newer['ticket']])

    def test_blocked_older_bundle_does_not_freeze_free_development(self):
        self.acquire(0, '--gui')
        self.assertEqual(self.acquire(1, '--gui', '--development')[0], 2)
        self.assertEqual(self.acquire(2, '--development')[0], 0)

    def test_wait_cancellation_refuses_missing_token_and_preserves_grant(self):
        held = self.acquire(0, '--gui')[1]['grant']
        waiting = self.acquire(1, '--gui')[1]['wait']
        self.assertEqual(self.cli('cancel-wait', '--token=' + waiting['token'])[0], 1)
        self.assertEqual(self.cli('cancel-wait', '--token=' + 'lost', '--confirmed', '--evidence', 'unknown')[0], 1)
        self.assertEqual(self.cli('release', '--token=' + waiting['token'], '--confirmed', '--evidence', 'wrong token type')[0], 1)
        self.assertEqual(self.acquire(1, '--development')[0], 1)
        self.assertEqual(self.cli('cancel-wait', '--token=' + waiting['token'], '--confirmed', '--evidence', 'No dispatch; request cancelled')[0], 0)
        self.assertEqual(self.cli('check', '--token=' + held['token'])[0], 0)
        self.assertEqual(self.cli('status')[1]['waiters'], [])

    def test_waiting_task_cannot_be_duplicated_by_new_attempt_or_main(self):
        self.acquire(0, '--gui')
        waiting = self.acquire(1, '--gui')[1]['wait']
        for changed in ({'attempt': 'attempt-2'}, {'coordinator': 'other-main'}):
            code, response = self.acquire(1, '--development', **changed)
            self.assertEqual(code, 2)
            self.assertEqual(response['reason'], 'task_has_waiting_owner_or_attempt')
            self.assertNotIn(waiting['token'], json.dumps(response))
        self.assertEqual(len(self.cli('status')[1]['waiters']), 1)

    def test_diagnose_read_only_unknown_liveness_and_release_owner(self):
        self.assertEqual(self.cli('diagnose')[1]['grants'], [])
        self.assertFalse(self.state.exists())
        grant = self.acquire(0, '--gui')[1]['grant']
        path = self.state / 'state.json'
        before = path.read_bytes()
        report = self.cli('diagnose')[1]
        self.assertEqual(report['recovery'][0]['liveness'], 'UNKNOWN_NOT_OBSERVED')
        self.assertEqual(path.read_bytes(), before)
        self.release(grant['token'])
        event = self.cli('status')[1]['events'][-1]
        self.assertEqual(event['owner']['project_root'], str(self.projects[0].resolve()))
        self.assertEqual(event['generation'], grant['generation'])

    def test_schema_two_migration_preserves_limits_and_tokens(self):
        grant = self.acquire(0, '--development')[1]['grant']
        path = self.state / 'state.json'
        state = json.loads(path.read_text())
        state['schema'] = 2
        for key in ('project_limit', 'project_limits', 'waiters', 'next_ticket'):
            state.pop(key)
        for event in state['events']:
            event.pop('owner')
        state['development_limit'] = 7
        path.write_text(json.dumps(state))
        before = path.read_bytes()
        self.assertEqual(self.cli('diagnose')[1]['development_limit'], 7)
        self.assertEqual(path.read_bytes(), before)
        self.acquire(1, '--gui')
        self.assertEqual(json.loads(path.read_text())['schema'], 3)
        self.assertEqual(self.cli('check', '--token=' + grant['token'])[0], 0)
        self.assertEqual(self.cli('status')[1]['development_limit'], 7)

    def test_malformed_wait_queue_fails_closed(self):
        import copy
        self.acquire(0, '--gui')
        self.acquire(1, '--gui')
        path = self.state / 'state.json'
        original = json.loads(path.read_text())
        for mutation in ('duplicate', 'ticket', 'slot', 'project_limit'):
            state = copy.deepcopy(original)
            if mutation == 'duplicate':
                state['waiters'].append(dict(state['waiters'][0]))
            elif mutation == 'ticket':
                state['waiters'][0]['ticket'] = 0
            elif mutation == 'slot':
                state['waiters'][0]['resources'] = ['development:1']
            else:
                state['project_limits'] = {'relative': 2}
            path.write_text(json.dumps(state))
            before = path.read_bytes()
            self.assertEqual(self.cli('status')[0], 1)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
