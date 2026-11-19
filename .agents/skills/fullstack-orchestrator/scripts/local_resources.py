#!/usr/bin/env python3
"""Cooperative local resource ownership. No daemon, expiry, process killing or dispatch.

Every participating coordinator must use the same state directory. Grants survive
caller exit and are not authentication or an OS sandbox. Store grant tokens in
project-native private task records; public status deliberately omits them.
"""
import argparse
import contextlib
import fcntl
import json
import math
import os
import re
from pathlib import Path
import secrets
import stat
import sys
import tempfile
import time
from filesystem_identity import canonical_directory, observed_path

DEFAULT_STATE = Path.home() / '.codex' / 'fullstack-orchestrator' / 'resources'
def strict_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def finite_timestamp(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


IDENTITY = ('project_root', 'coordinator', 'task', 'attempt', 'operation')


def fresh_state():
    return dict(schema=3, generation=0, grants=[], development_limit=4,
                project_limit=2, project_limits={}, events=[], waiters=[], next_ticket=0)


class CoordinationError(ValueError):
    pass


def text(value, name, maximum=240):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise CoordinationError(f'invalid {name}')
    return value


def directory(value):
    return canonical_directory(value)


def same_project(left, right):
    return observed_path(left) == observed_path(right)


def normalized_resources(values):
    return sorted('workspace:' + observed_path(v[len('workspace:'):])
                  if v.startswith('workspace:') else v for v in values)


def regular_private(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1:
        raise CoordinationError(f'unsafe state file: {path.name}')


def normalized_absolute(value):
    return isinstance(value, str) and value.startswith('/') and value == os.path.normpath(value) and not value.startswith('//')


def resource_key(value):
    value = text(value, 'resource', 4096)
    if value == 'gui:host' or re.fullmatch(r'development:[1-9][0-9]{0,2}', value):
        return value
    if value.startswith('exclusive:'):
        text(value[len('exclusive:'):], 'exclusive key', 4086)
        return value
    if value.startswith('workspace:'):
        path = value[len('workspace:'):]
        if normalized_absolute(path) and path != '/':
            return value
    raise CoordinationError('invalid reserved resource key')


def resources_overlap(left, right):
    if left == right:
        return True
    if left.startswith('workspace:') and right.startswith('workspace:'):
        a, b = (Path(observed_path(value[len('workspace:'):])) for value in (left, right))
        return a == b or a in b.parents or b in a.parents
    return False


def validate(state):
    if not isinstance(state, dict) or type(state.get('schema')) is not int or state['schema'] not in (1, 2, 3) or type(state.get('generation')) is not int or state['generation'] < 0 or not isinstance(state.get('grants'), list):
        raise CoordinationError('invalid resource state schema')
    if state['schema'] >= 2:
        if type(state.get('development_limit')) is not int or not 1 <= state['development_limit'] <= 256:
            raise CoordinationError('invalid development limit (1..256)')
        events = state.get('events')
        if not isinstance(events, list) or len(events) > 100:
            raise CoordinationError('invalid bounded event history')
        for event in events:
            expected = {'action', 'time', 'generation', 'evidence'}
            if state['schema'] == 3:
                expected.add('owner')
            if not isinstance(event, dict) or set(event) != expected or event['action'] not in ('configure', 'acquire', 'release', 'wait', 'cancel_wait'):
                raise CoordinationError('invalid event')
            if state['schema'] == 3 and event['owner'] is not None:
                validate_identity(event['owner'])
            text(event['evidence'], 'event evidence', 500)
            if not finite_timestamp(event['time']) or type(event['generation']) is not int or not 0 <= event['generation'] <= state['generation']:
                raise CoordinationError('invalid event identity')
    tokens, identities, keys, generations, owners = set(), set(), set(), set(), {}
    for grant in state['grants']:
        if not isinstance(grant, dict):
            raise CoordinationError('invalid grant')
        identity = validate_identity({k: grant.get(k) for k in IDENTITY})
        if not normalized_absolute(grant['project_root']) or grant['project_root'] == '/':
            raise CoordinationError('invalid project root in state')
        token = text(grant.get('token'), 'token')
        resources = grant.get('resources')
        if not isinstance(resources, list) or not resources:
            raise CoordinationError('invalid grant resources')
        for resource in resources:
            resource_key(resource)
            if resource.startswith('development:') and int(resource.split(':')[1]) > (2 if state['schema'] == 1 else 256):
                raise CoordinationError('invalid development slot')
        if resources != sorted(set(resources)):
            raise CoordinationError('duplicate or unsorted grant resources')
        if sum(r.startswith('development:') for r in resources) > 1:
            raise CoordinationError('one grant cannot own two development slots')
        if token in tokens or identity in identities or any(resources_overlap(a, b) for a in keys for b in resources):
            raise CoordinationError('conflicting resource state')
        if type(grant.get('generation')) is not int or not 0 < grant['generation'] <= state['generation'] or grant['generation'] in generations:
            raise CoordinationError('invalid or duplicate grant generation')
        task = (observed_path(grant['project_root']), grant['task'])
        owner = (grant['coordinator'], grant['attempt'])
        if task in owners and owners[task] != owner:
            raise CoordinationError('conflicting task owner or attempt in state')
        owners[task] = owner
        if not finite_timestamp(grant.get('created_at')):
            raise CoordinationError('invalid observation time')
        tokens.add(token)
        identities.add(identity)
        keys.update(resources)
        generations.add(grant['generation'])
    if state['schema'] == 3:
        limit_value(state.get('project_limit'))
        overrides = state.get('project_limits')
        if not isinstance(overrides, dict):
            raise CoordinationError('invalid project limit map')
        for path, limit in overrides.items():
            if not normalized_absolute(path) or path == '/':
                raise CoordinationError('invalid project limit root')
            limit_value(limit)
        if type(state.get('next_ticket')) is not int or state['next_ticket'] < 0:
            raise CoordinationError('invalid next queue ticket')
        waiters = state.get('waiters')
        if not isinstance(waiters, list) or len(waiters) > 1000:
            raise CoordinationError('invalid bounded wait queue')
        last = 0
        for waiter in waiters:
            if not isinstance(waiter, dict):
                raise CoordinationError('invalid waiter')
            identity = validate_identity({k: waiter.get(k) for k in IDENTITY})
            task = (observed_path(waiter['project_root']), waiter['task'])
            owner = (waiter['coordinator'], waiter['attempt'])
            if task in owners and owners[task] != owner:
                raise CoordinationError('conflicting waiting task owner or attempt')
            owners[task] = owner
            if identity in identities:
                raise CoordinationError('duplicate active or waiting identity')
            identities.add(identity)
            token = text(waiter.get('token'), 'wait token')
            if token in tokens:
                raise CoordinationError('duplicate wait token')
            tokens.add(token)
            ticket = waiter.get('ticket')
            if type(ticket) is not int or not last < ticket <= state['next_ticket']:
                raise CoordinationError('invalid queue ordering')
            last = ticket
            if type(waiter.get('development')) is not bool or not finite_timestamp(waiter.get('created_at')):
                raise CoordinationError('invalid waiter request')
            req = waiter.get('resources')
            if not isinstance(req, list) or any(not isinstance(r, str) for r in req) or req != sorted(set(req)) or (not req and not waiter['development']):
                raise CoordinationError('invalid waiter resources')
            for r in req:
                resource_key(r)
                if r.startswith('development:'):
                    raise CoordinationError('waiter cannot reserve development slot')
    return state


def limit_value(value):
    if type(value) is not int or not 1 <= value <= 256:
        raise CoordinationError('limit must be an integer in 1..256')
    return value


def validate_identity(identity):
    if not isinstance(identity, dict) or set(identity) != set(IDENTITY):
        raise CoordinationError('invalid identity')
    result = tuple(text(identity[k], k, 4096 if k == 'project_root' else 240) for k in IDENTITY)
    if not normalized_absolute(identity['project_root']) or identity['project_root'] == '/':
        raise CoordinationError('invalid identity project root')
    return (observed_path(identity['project_root']), *result[1:])


@contextlib.contextmanager
def transaction(state_dir, initialize=True):
    root = Path(state_dir).expanduser().absolute()
    if root.is_symlink():
        raise CoordinationError('linked state directory refused')
    if not root.exists() and not initialize:
        yield root, fresh_state()
        return
    if initialize:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Resolve ancestor aliases once (macOS /var is commonly /private/var).
    # The leaf is refused above; this is binding, not a hostile-ancestor sandbox.
    root = root.resolve(strict=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise CoordinationError('state directory must be owned by current user and private (0700)')
    lock = root / 'transaction.lock'
    if lock.is_symlink():
        raise CoordinationError('linked transaction lock refused')
    if not lock.exists():
        if (root / 'state.json').exists() or (root / 'state.json').is_symlink():
            raise CoordinationError('resource state has no stable lock; reconcile manually')
        if not initialize:
            yield root, fresh_state()
            return
    fd = os.open(lock, os.O_RDWR | (os.O_CREAT if initialize else 0) | os.O_NOFOLLOW, 0o600)
    try:
        regular_private(lock)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        descriptor, pathname = os.fstat(fd), lock.lstat()
        if (descriptor.st_dev, descriptor.st_ino) != (pathname.st_dev, pathname.st_ino):
            raise CoordinationError('stable lock identity changed; reconcile manually')
        # A stable lock file is never unlinked, including when no grants remain.
        path = root / 'state.json'
        if path.exists() or path.is_symlink():
            regular_private(path)
            if path.stat().st_size > 8 * 1024 * 1024:
                raise CoordinationError('resource state exceeds size limit')
            with path.open(encoding='utf-8') as stream:
                state = validate(json.load(stream, object_pairs_hook=strict_pairs, parse_constant=reject_constant))
        else:
            if os.fstat(fd).st_size:
                raise CoordinationError('previously initialized resource state is missing; reconcile manually')
            state = fresh_state()
        yield root, state
    finally:
        os.close(fd)


def save(root, state):
    validate(state)
    fd, name = tempfile.mkstemp(prefix='.state-', dir=root)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream, ensure_ascii=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, root / 'state.json')
        marker = os.open(root / 'transaction.lock', os.O_WRONLY | os.O_NOFOLLOW)
        try:
            os.write(marker, b'initialized\n')
            os.fsync(marker)
        finally:
            os.close(marker)
        folder = os.open(root, os.O_RDONLY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def public(grant):
    return {key: value for key, value in grant.items() if key != 'token'}


def upgrade(state):
    if state['schema'] == 1:
        state.update(schema=2, development_limit=2, events=[])
    if state['schema'] == 2:
        state.update(schema=3, project_limit=2, project_limits={}, waiters=[], next_ticket=0)
        for entry in state['events']:
            entry['owner'] = None


def event(state, action, evidence, generation=None, owner=None):
    upgrade(state)
    state['events'] = (state['events'] + [dict(action=action, time=time.time(), generation=state['generation'] if generation is None else generation, evidence=evidence, owner={k: owner[k] for k in IDENTITY} if owner else None)])[-100:]


def bundle_conflicts(state, request):
    occupied = {r for g in state['grants'] for r in g['resources']}
    conflicts = {r for r in request['resources'] if any(resources_overlap(r, held) for held in occupied)}
    for grant in state['grants']:
        if same_project(grant['project_root'], request['project_root']) and grant['task'] == request['task'] and (grant['coordinator'], grant['attempt']) != (request['coordinator'], request['attempt']):
            conflicts.add('task_has_active_owner_or_attempt')
    if request['development']:
        active = [g for g in state['grants'] if any(r.startswith('development:') for r in g['resources'])]
        if len(active) >= state.get('development_limit', 2):
            conflicts.add('development:capacity')
        project_cap = min((limit for path, limit in state.get('project_limits', {}).items()
                           if same_project(path, request['project_root'])), default=state.get('project_limit', 2))
        if sum(same_project(g['project_root'], request['project_root']) for g in active) >= project_cap:
            conflicts.add('development:project_capacity')
    return conflicts


def competing(a, b):
    return (a['development'] and b['development']) or any(resources_overlap(x, y) for x in a['resources'] for y in b['resources']) or (same_project(a['project_root'], b['project_root']) and a['task'] == b['task'])


def run(args):
    if args.command == 'acquire':
        identity = {'project_root': directory(args.project_root)}
        for field in ('coordinator', 'task', 'attempt', 'operation'):
            identity[field] = text(getattr(args, field), field)
        resources = set()
        for resource in args.resource:
            resource = text(resource, 'resource', 4096)
            if not resource.startswith('exclusive:') or resource == 'exclusive:':
                raise CoordinationError('custom resource must use exclusive:<stable-key>')
            resources.add(resource)
        if args.write_workspace:
            resources.add('workspace:' + directory(args.write_workspace))
        if args.gui:
            resources.add('gui:host')
        requested = sorted(resources)
        if not requested and not args.development:
            raise CoordinationError('request at least one resource')
    with transaction(args.state_dir, initialize=args.command in ('acquire', 'configure')) as (root, state):
        if args.command in ('status', 'diagnose'):
            result = {'status': 'OBSERVED', 'development_limit': state.get('development_limit', 2), 'project_limit': state.get('project_limit', 2), 'project_limits': state.get('project_limits', {}), 'grants': [public(g) for g in state['grants']], 'waiters': [public(w) for w in state.get('waiters', [])], 'events': state.get('events', []), 'automatic_expiry': False}
            if args.command == 'diagnose':
                result['recovery'] = [{'generation': g['generation'], 'owner': {k: g[k] for k in IDENTITY}, 'required': ['Locate matching project-local task and external handle', 'Observe every resource in this bundle no longer in use; closed delivery subset is insufficient', 'Reconcile side effects and candidate', 'Use original token and release confirmation; missing token requires human recovery'], 'liveness': 'UNKNOWN_NOT_OBSERVED'} for g in state['grants']]
                result['waiting_recovery'] = 'Queued requests never dispatch automatically; original Main retries or cancels its wait token. No age-based removal.'
            return result
        if args.command == 'configure':
            if not args.confirmed:
                raise CoordinationError('configure requires --confirmed and task-authorized host policy')
            text(args.evidence, 'configuration evidence', 500)
            if args.development_limit is None and args.project_limit is None:
                raise CoordinationError('configure at least one limit')
            if (args.project_root is None) != (args.project_limit is None):
                raise CoordinationError('project-root and project-limit must be supplied together')
            if args.development_limit is not None:
                limit_value(args.development_limit)
            if args.project_limit is not None:
                limit_value(args.project_limit)
            project = directory(args.project_root) if args.project_root else None
            upgrade(state)
            if args.development_limit is not None:
                state['development_limit'] = args.development_limit
            if project:
                for path in list(state['project_limits']):
                    if same_project(path, project):
                        del state['project_limits'][path]
                state['project_limits'][project] = args.project_limit
            event(state, 'configure', args.evidence)
            save(root, state)
            return {'status': 'CONFIGURED', 'development_limit': state['development_limit'], 'project_limits': state['project_limits'], 'active_grants_preserved': True}
        if args.command == 'acquire':
            for grant in state['grants']:
                same_identity = validate_identity({k: grant[k] for k in IDENTITY}) == validate_identity(identity)
                if same_identity:
                    expected = [r for r in grant['resources'] if not r.startswith('development:')]
                    had_dev = any(r.startswith('development:') for r in grant['resources'])
                    if normalized_resources(expected) != normalized_resources(requested) or had_dev != args.development:
                        raise CoordinationError('same identity already owns a different resource bundle')
                    return {'status': 'GRANTED', 'idempotent': True, 'grant': grant}
                same_task = same_project(grant['project_root'], identity['project_root']) and grant['task'] == identity['task']
                same_owner = grant['coordinator'] == identity['coordinator'] and grant['attempt'] == identity['attempt']
                if same_task and (not same_owner or (grant['operation'] == 'execution' and identity['operation'] == 'execution')):
                    return {'status': 'BUSY', 'reason': 'task_has_active_owner_or_attempt', 'owner': public(grant)}
            upgrade(state)
            for pending in state['waiters']:
                same_task = same_project(pending['project_root'], identity['project_root']) and pending['task'] == identity['task']
                same_owner = (pending['coordinator'], pending['attempt']) == (identity['coordinator'], identity['attempt'])
                if same_task and not same_owner:
                    return {'status': 'BUSY', 'reason': 'task_has_waiting_owner_or_attempt', 'owner': public(pending)}
            request = dict(identity, resources=requested, development=args.development)
            waiter = next((w for w in state['waiters'] if validate_identity({k: w[k] for k in IDENTITY}) == validate_identity(identity)), None)
            if waiter and (normalized_resources(waiter['resources']) != normalized_resources(requested) or waiter['development'] != args.development):
                raise CoordinationError('waiting identity already has a different resource bundle; cancel wait first')
            conflicts = bundle_conflicts(state, request)
            earlier = state['waiters'][:state['waiters'].index(waiter)] if waiter else state['waiters']
            blockers = [w['ticket'] for w in earlier if competing(w, request) and not bundle_conflicts(state, w)]
            if blockers:
                conflicts.add('queue:earlier_eligible_request')
            if conflicts:
                if waiter is None:
                    if len(state['waiters']) >= 1000:
                        raise CoordinationError('wait queue full; no dispatch')
                    state['next_ticket'] += 1
                    waiter = dict(request, token='wait_' + secrets.token_urlsafe(32), ticket=state['next_ticket'], created_at=time.time())
                    state['waiters'].append(waiter)
                    event(state, 'wait', 'Request waits; no resources held or automatic dispatch', owner=identity)
                    save(root, state)
                return {'status': 'BUSY', 'resources': sorted(conflicts), 'wait': waiter, 'earlier_eligible_tickets': blockers, 'automatic_dispatch': False}
            if waiter:
                state['waiters'].remove(waiter)
            if args.development:
                occupied = {r for g in state['grants'] for r in g['resources']}
                resources.add(next(f'development:{n}' for n in range(1, state['development_limit'] + 1) if f'development:{n}' not in occupied))
            state['generation'] += 1
            grant = dict(identity, token='grant_' + secrets.token_urlsafe(32), generation=state['generation'], resources=sorted(resources), created_at=time.time())
            state['grants'].append(grant)
            event(state, 'acquire', 'Resource grant created; task details remain project-local', owner=identity)
            save(root, state)
            return {'status': 'GRANTED', 'idempotent': False, 'grant': grant}
        if args.command == 'cancel-wait':
            token = text(args.token, 'wait token')
            waiter = next((w for w in state.get('waiters', []) if secrets.compare_digest(w['token'], token)), None)
            if waiter is None or not args.confirmed:
                raise CoordinationError('cancel-wait requires original wait token and confirmation')
            text(args.evidence, 'wait cancellation evidence', 500)
            state['waiters'].remove(waiter)
            event(state, 'cancel_wait', args.evidence, owner=waiter)
            save(root, state)
            return {'status': 'WAIT_CANCELLED', 'ticket': waiter['ticket']}
        token = text(args.token, 'token')
        grant = next((g for g in state['grants'] if secrets.compare_digest(g['token'], token)), None)
        if grant is None:
            raise CoordinationError('unknown or released grant token; reconcile ownership')
        if args.command == 'check':
            return {'status': 'OWNED', 'grant': public(grant)}
        if not args.confirmed:
            raise CoordinationError('release requires --confirmed after actual execution reconciliation')
        text(args.evidence, 'release evidence', 500)
        state['grants'].remove(grant)
        event(state, 'release', args.evidence, grant['generation'], owner=grant)
        save(root, state)
        return {'status': 'RELEASED', 'generation': grant['generation'], 'evidence': args.evidence}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CoordinationError(message)


def parser():
    result = Parser(description=__doc__)
    result.add_argument('--state-dir', default=str(DEFAULT_STATE))
    commands = result.add_subparsers(dest='command', required=True, parser_class=Parser)
    acquire = commands.add_parser('acquire')
    for flag in ('project-root', 'coordinator', 'task', 'attempt'):
        acquire.add_argument('--' + flag, required=True)
    acquire.add_argument('--operation', default='execution')
    acquire.add_argument('--development', action='store_true')
    acquire.add_argument('--gui', action='store_true')
    acquire.add_argument('--write-workspace')
    acquire.add_argument('--resource', action='append', default=[])
    commands.add_parser('status')
    commands.add_parser('diagnose')
    configure = commands.add_parser('configure')
    configure.add_argument('--development-limit', type=int)
    configure.add_argument('--project-root')
    configure.add_argument('--project-limit', type=int)
    configure.add_argument('--confirmed', action='store_true')
    configure.add_argument('--evidence', default='')
    for name in ('check', 'release', 'cancel-wait'):
        command = commands.add_parser(name)
        command.add_argument('--token', required=True)
        if name in ('release', 'cancel-wait'):
            command.add_argument('--confirmed', action='store_true')
            command.add_argument('--evidence', default='')
    return result


def main(argv=None):
    try:
        response = run(parser().parse_args(argv))
        print(json.dumps(response, ensure_ascii=False, sort_keys=True))
        return 2 if response['status'] == 'BUSY' else 0
    except BlockingIOError:
        print(json.dumps({'status': 'BUSY', 'reason': 'coordination_transaction_busy_retry_without_dispatch'}))
        return 2
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({'status': 'ERROR', 'reason': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
