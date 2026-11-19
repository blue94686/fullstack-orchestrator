import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from init_shared_exchange import DIRECTORIES, initialize


class SharedExchangeInitializerTests(unittest.TestCase):
    def test_cli_requires_explicit_root_instead_of_using_shell_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(__file__).with_name("init_shared_exchange.py")
            result = subprocess.run([sys.executable, "-B", str(script)], cwd=directory,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(directory) / "shared").exists())

    def test_explicit_product_root_with_spaces_and_unicode_from_other_cwd(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            product = base / "毕业设计 space" / "设计" / "campus_qa"
            product.mkdir(parents=True)
            script = Path(__file__).with_name("init_shared_exchange.py")
            result = subprocess.run([sys.executable, "-B", str(script), str(product)],
                                    cwd=base, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["project_root"], str(product.resolve()))
            self.assertTrue((product / "shared" / "README.md").is_file())
            self.assertFalse((base / "shared").exists())

    def test_peer_creation_during_initialize_preserves_peer_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            original_mkdir, original_open = Path.mkdir, Path.open
            raced_directory = root / "shared" / "inputs"
            raced_readme = root / "shared" / "README.md"

            def peer_mkdir(path, *args, **kwargs):
                if path == raced_directory and not path.exists():
                    original_mkdir(path.parent, parents=True, exist_ok=True)
                    original_mkdir(path)
                return original_mkdir(path, *args, **kwargs)

            def peer_open(path, mode="r", *args, **kwargs):
                if path == raced_readme and mode == "x" and not path.exists():
                    with original_open(path, "w", encoding="utf-8") as handle:
                        handle.write("peer project instructions\n")
                return original_open(path, mode, *args, **kwargs)

            with patch.object(Path, "mkdir", peer_mkdir), patch.object(Path, "open", peer_open):
                result = initialize(root)
            self.assertFalse(result["readme_created"])
            self.assertEqual(raced_readme.read_text(), "peer project instructions\n")
            self.assertNotIn("inputs", result["created_directories"])

    def test_creates_project_relative_structure_and_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            result = initialize(Path(directory))
            shared = Path(directory) / "shared"
            self.assertEqual(result["result"], "CREATED_OR_REUSED")
            self.assertTrue(result["readme_created"])
            self.assertTrue(all((shared / relative).is_dir() for relative in DIRECTORIES))
            self.assertTrue((shared / "README.md").is_file())

    def test_repeat_preserves_existing_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            initialize(Path(directory))
            readme = Path(directory) / "shared" / "README.md"
            readme.write_text("project-owned instructions\n", encoding="utf-8")
            result = initialize(Path(directory))
            self.assertFalse(result["readme_created"])
            self.assertTrue(result["existing_content_preserved"])
            self.assertEqual(readme.read_text(encoding="utf-8"), "project-owned instructions\n")

    def test_rejects_filesystem_root(self):
        with self.assertRaises(ValueError):
            initialize(Path("/"))

    def test_rejects_symlinks_without_writing_targets(self):
        for relative in ("shared", "shared/artifacts", "shared/artifacts/gemini",
                         "shared/README.md"):
            for dangling in (False, True):
                with self.subTest(relative=relative, dangling=dangling):
                    with tempfile.TemporaryDirectory() as directory:
                        base = Path(directory)
                        project = base / "project"
                        project.mkdir()
                        target = base / "outside"
                        if not dangling:
                            target.mkdir()
                        link = project / relative
                        link.parent.mkdir(parents=True, exist_ok=True)
                        link.symlink_to(target, target_is_directory=True)
                        before = sorted(str(p.relative_to(project)) for p in project.rglob("*"))
                        with self.assertRaises(ValueError):
                            initialize(project)
                        self.assertEqual(before, sorted(str(p.relative_to(project))
                                                       for p in project.rglob("*")))
                        self.assertEqual(list(target.iterdir()) if target.exists() else [], [])
                        self.assertEqual(target.exists(), not dangling)

    def test_collision_is_detected_before_creating_other_directories(self):
        for relative in ("shared", "shared/acceptance", "shared/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    project = Path(directory)
                    conflict = project / relative
                    conflict.parent.mkdir(parents=True, exist_ok=True)
                    conflict.write_bytes(b"keep these bytes")
                    before = sorted(str(p.relative_to(project)) for p in project.rglob("*"))
                    with self.assertRaises(ValueError):
                        initialize(project)
                    self.assertEqual(conflict.read_bytes(), b"keep these bytes")
                    self.assertEqual(before, sorted(str(p.relative_to(project))
                                                   for p in project.rglob("*")))


if __name__ == "__main__":
    unittest.main()
