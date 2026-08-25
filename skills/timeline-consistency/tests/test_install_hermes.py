from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.install_hermes import install


class InstallHermesTests(unittest.TestCase):
    def test_install_is_idempotent_and_does_not_auto_enable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            hermes_home = Path(temporary) / "profile"
            first = install(hermes_home)
            self.assertTrue((hermes_home / "skills" / "timeline-consistency" / "SKILL.md").is_file())
            self.assertTrue((hermes_home / "plugins" / "timeline-consistency" / "plugin.yaml").is_file())
            self.assertFalse((hermes_home / "config.yaml").exists())
            self.assertTrue(any("已安装 Skill" in message for message in first))

            second = install(hermes_home)
            self.assertTrue(all("相同版本" in message for message in second))

    def test_conflict_blocks_all_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            hermes_home = Path(temporary) / "profile"
            skill_target = hermes_home / "skills" / "timeline-consistency"
            skill_target.mkdir(parents=True)
            (skill_target / "SKILL.md").write_text("用户修改", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                install(hermes_home)
            self.assertFalse((hermes_home / "plugins" / "timeline-consistency").exists())
            self.assertEqual((skill_target / "SKILL.md").read_text(encoding="utf-8"), "用户修改")

    def test_dry_run_does_not_create_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            hermes_home = Path(temporary) / "profile"
            messages = install(hermes_home, dry_run=True)
            self.assertFalse(hermes_home.exists())
            self.assertEqual(len(messages), 2)

    def test_symlink_destination_is_a_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hermes_home = root / "profile"
            plugin_target = hermes_home / "plugins" / "timeline-consistency"
            plugin_target.parent.mkdir(parents=True)
            plugin_target.symlink_to(root / "missing-plugin", target_is_directory=True)

            with self.assertRaises(FileExistsError):
                install(hermes_home)
            self.assertTrue(plugin_target.is_symlink())
            self.assertFalse((hermes_home / "skills" / "timeline-consistency").exists())


if __name__ == "__main__":
    unittest.main()
