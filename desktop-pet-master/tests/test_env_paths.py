import tempfile
import unittest
from pathlib import Path

from moodpet.env_paths import resolve_env_path


class EnvPathsTest(unittest.TestCase):
    def test_resolve_env_path_finds_parent_workspace_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            app_dir = workspace / "desktop-pet-master"
            app_dir.mkdir()
            env_path = workspace / ".env"
            env_path.write_text("ARK_API_KEY=abc\n", encoding="utf-8")

            self.assertEqual(resolve_env_path(app_dir), env_path)


if __name__ == "__main__":
    unittest.main()
