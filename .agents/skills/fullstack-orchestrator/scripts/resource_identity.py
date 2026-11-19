#!/usr/bin/env python3
"""Generate cooperative resource identities without reading state or contacting services.

All callers must use this version and the same nonsecret deployment/instance names.
Keys do not discover remote aliases, enforce OS permissions, or lock resources.
Client keys deliberately remain app-instance-wide even for known sessions: mixing
coarse/fine keys cannot safely exclude with an exact-match resource coordinator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from filesystem_identity import canonical_directory


class IdentityError(ValueError):
    pass


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes invalid values, which may contain credentials.
        raise IdentityError('invalid command arguments; use --help for syntax')


def clean(value, field):
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 2048:
        raise IdentityError('invalid ' + field)
    if any(unicodedata.category(c).startswith('C') for c in value):
        raise IdentityError('control characters forbidden in ' + field)
    if '://' in value or any(c in value for c in '@?#') or re.search(r'(?i)(password|passwd|token|secret|api[_-]?key)\s*[:=]', value):
        raise IdentityError('URLs and credentials forbidden in ' + field)
    return value


def label(value, field):
    value = clean(value, field)
    if not re.fullmatch(r'[\w.:-]+', value, re.UNICODE):
        raise IdentityError('use a nonsecret identifier for ' + field)
    return value


def directory(value, field):
    clean(value, field)
    try:
        path = Path(canonical_directory(value))
    except (OSError, RuntimeError) as error:
        raise IdentityError('invalid existing directory for ' + field) from error
    if not path.is_dir() or path.parent == path:
        raise IdentityError(field + ' must be an existing non-root directory')
    clean(str(path), field)
    return str(path)


def identity(kind, parts, **metadata):
    canonical = json.dumps(parts, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    key = 'exclusive:resource-v1:' + kind + ':' + digest
    return dict(schema='resource-identity-v1', kind=kind, resource=key,
                identity=parts, **metadata)


def generate(args):
    if args.kind == 'port':
        host = label(args.host, 'host').lower()
        # These are local host aliases, never remote-interface or DNS discovery.
        if host in ('local', 'localhost', '127.0.0.1', '::1'):
            host = 'local'
        clean(args.bind, 'bind')
        if not re.fullmatch(r'[A-Za-z0-9_.:\[\]*-]+', args.bind):
            raise IdentityError('invalid bind address')
        if not 1 <= args.port <= 65535:
            raise IdentityError('port must be 1..65535')
        return identity('port', dict(host=host, protocol=args.protocol.lower(), port=args.port),
                        policy='all bind addresses share one host/protocol/port key')
    if args.kind == 'database':
        deployment = label(args.deployment, 'deployment')
        engine = label(args.engine, 'engine').lower()
        engine = {'postgresql': 'postgres', 'mariadb': 'mysql'}.get(engine, engine)
        # Keep name case: engines/deployments differ in identifier case semantics.
        return identity('database', dict(deployment=deployment, engine=engine,
                                        database=label(args.database, 'database')))
    if args.kind == 'compose':
        root = directory(args.project_root, 'project root')
        name = label(args.project_name, 'project name')
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', name):
            raise IdentityError('Compose project name must be explicit normalized lowercase')
        # Compose resource collisions follow daemon + name, not source directory.
        return identity('compose', dict(daemon=label(args.daemon, 'daemon'), project_name=name),
                        project_root=root,
                        policy='same daemon and project name conflict across source roots')
    if args.kind == 'profile':
        return identity('profile', dict(path=directory(args.path, 'profile')))
    if args.kind == 'client':
        parts = dict(app=label(args.app, 'app').lower(), instance=label(args.instance, 'instance'))
        session = label(args.session, 'session') if args.session is not None else None
        return identity('client', parts, session=session, policy='app-instance-exclusive',
                        limitation='session metadata never relaxes app-instance exclusion')
    raise IdentityError('unsupported resource kind')


def parser():
    result = SafeParser(description=__doc__)
    sub = result.add_subparsers(dest='kind', required=True)
    port = sub.add_parser('port')
    port.add_argument('--host', default='local', help='nonsecret host namespace; no DNS lookup')
    port.add_argument('--protocol', type=str.lower, choices=('tcp', 'udp'), default='tcp')
    port.add_argument('--port', type=int, required=True)
    port.add_argument('--bind', default='*', help='validated but conservatively ignored in key')
    database = sub.add_parser('database')
    for name in ('deployment', 'engine', 'database'):
        database.add_argument('--' + name, required=True)
    compose = sub.add_parser('compose')
    compose.add_argument('--project-root', required=True)
    compose.add_argument('--project-name', required=True)
    compose.add_argument('--daemon', default='local', help='nonsecret daemon identity, not a URL')
    profile = sub.add_parser('profile')
    profile.add_argument('--path', required=True)
    client = sub.add_parser('client')
    client.add_argument('--app', required=True)
    client.add_argument('--instance', required=True)
    client.add_argument('--session')
    return result


def main():
    try:
        result = generate(parser().parse_args())
    except (IdentityError, OSError, ValueError) as error:
        # Do not echo rejected potentially secret values.
        print(json.dumps(dict(error=str(error)), ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
