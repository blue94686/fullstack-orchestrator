"""Actual CLI tests. All filesystem writes are inside temporary directories."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('resource_identity.py')


class ResourceIdentityTests(unittest.TestCase):
    def test_profile_firmlink_identity(self):
        with tempfile.TemporaryDirectory(dir=Path.home()) as temp:
            path = Path(temp).resolve()
            alias = Path('/System/Volumes/Data') / str(path).lstrip('/')
            if not alias.is_dir() or not alias.samefile(path):
                self.skipTest('APFS firmlink alias unavailable')
            self.assertEqual(self.key('profile', '--path', path), self.key('profile', '--path', alias))

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr + result.stdout)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def key(self, *args):
        value = self.cli(*args)
        self.assertTrue(value['resource'].startswith('exclusive:resource-v1:'))
        return value['resource']

    def test_local_bind_aliases(self):
        keys = {self.key('port', '--port', '3000', '--bind', bind)
                for bind in ('localhost', '127.0.0.1', '0.0.0.0', '::1', '::', '[::]', '*')}
        keys.update(self.key('port', '--port', '3000', '--host', host)
                    for host in ('LOCAL', 'localhost', '127.0.0.1', '::1'))
        self.assertEqual(len(keys), 1)

    def test_ports_and_protocols_and_remote_host(self):
        self.assertEqual(len({self.key('port', '--port', port, '--protocol', protocol, '--host', host)
                              for port in ('3000', '3001') for protocol in ('tcp', 'udp')
                              for host in ('local', 'remote-a')}), 8)
        for port in ('0', '-1', '65536'):
            self.cli('port', '--port', port, ok=False)

    def test_database_engine_alias_and_explicit_identity(self):
        base = ('database', '--deployment', 'dev', '--database', 'Campus')
        self.assertEqual(self.key(*base, '--engine', 'postgresql'), self.key(*base, '--engine', 'POSTGRES'))
        self.assertNotEqual(self.key(*base, '--engine', 'postgres'),
                            self.key('database', '--deployment', 'prod', '--database', 'Campus', '--engine', 'postgres'))
        self.assertNotEqual(self.key(*base, '--engine', 'postgres'),
                            self.key('database', '--deployment', 'dev', '--database', 'campus', '--engine', 'postgres'))

    def test_reject_secret_or_url_or_control(self):
        for bad in ('postgres://user:password@host/db', 'user@host', 'token=abc', 'password:abc',
                    'abc\nxyz', 'abc\x00xyz', 'abc\u202exyz', 'host?password=x', ' host'):
            if '\x00' in bad:  # OS argv cannot carry NUL; exercise validation directly.
                import importlib.util
                spec = importlib.util.spec_from_file_location('identity', SCRIPT)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                with self.assertRaises(module.IdentityError):
                    module.clean(bad, 'test')
                continue
            result = self.cli('database', '--deployment', bad, '--engine', 'postgres', '--database', 'db', ok=False)
            self.assertNotIn(bad, result['error'])
        self.cli('port', '--port', '42', '--bind', 'https://example.com', ok=False)
        self.cli('client', '--app', 'gemini', '--instance', 'token=abc', ok=False)

    def test_compose_same_daemon_name_cross_roots_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            a, b = Path(temporary) / 'a', Path(temporary) / 'b'
            a.mkdir(); b.mkdir()
            one = self.cli('compose', '--project-root', a, '--project-name', 'dev')
            two = self.cli('compose', '--project-root', b, '--project-name', 'dev')
            self.assertEqual(one['resource'], two['resource'])
            self.assertNotEqual(one['project_root'], two['project_root'])
            self.assertNotEqual(one['resource'], self.key('compose', '--project-root', a, '--project-name', 'dev', '--daemon', 'other'))
            self.cli('compose', '--project-root', a, '--project-name', 'Dev', ok=False)

    def test_profile_and_compose_resolve_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'; profile.mkdir()
            alias = root / 'alias'; alias.symlink_to(profile, target_is_directory=True)
            self.assertEqual(self.key('profile', '--path', profile), self.key('profile', '--path', alias))
            self.assertEqual(self.cli('compose', '--project-root', alias, '--project-name', 'dev')['project_root'], str(profile.resolve()))
            self.cli('profile', '--path', root / 'missing', ok=False)
            regular = root / 'file'; regular.write_text('x')
            self.cli('profile', '--path', regular, ok=False)
            self.cli('profile', '--path', '/', ok=False)

    def test_profile_case_alias_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            actual = Path(temporary) / 'CaseProfile'; actual.mkdir()
            alias = Path(temporary) / 'caseprofile'
            if not alias.exists():
                self.skipTest('case-sensitive filesystem')
            self.assertEqual(self.key('profile', '--path', actual),
                             self.key('profile', '--path', alias))

    def test_profile_unicode_alias_identity(self):
        import unicodedata
        with tempfile.TemporaryDirectory() as temporary:
            actual = Path(temporary) / 'Caf\u00e9'; actual.mkdir()
            alias = Path(temporary) / unicodedata.normalize('NFD', actual.name)
            if not alias.exists() or not actual.samefile(alias):
                self.skipTest('filesystem treats Unicode spellings as distinct')
            self.assertEqual(self.key('profile', '--path', actual),
                             self.key('profile', '--path', alias))

    def test_client_same_instance_all_sessions_serial(self):
        base = ('client', '--app', 'Gemini', '--instance', 'default')
        keys = {self.key(*base), self.key(*base, '--session', 'one'), self.key(*base, '--session', 'two')}
        self.assertEqual(len(keys), 1)
        self.assertNotEqual(self.key(*base), self.key('client', '--app', 'gemini', '--instance', 'other'))

    def test_tuple_encoding_avoids_delimiter_collision(self):
        self.assertNotEqual(self.key('database', '--deployment', 'a:b', '--engine', 'c', '--database', 'd'),
                            self.key('database', '--deployment', 'a', '--engine', 'b:c', '--database', 'd'))

    def test_invalid_arguments_do_not_echo_secret(self):
        for args in (('port', '--port', 'password=abc'),
                     ('client', '--app', 'gemini'),
                     ('unknown-password=abc',)):
            value = self.cli(*args, ok=False)
            self.assertNotIn('password=abc', value['error'])


if __name__ == '__main__':
    unittest.main()
