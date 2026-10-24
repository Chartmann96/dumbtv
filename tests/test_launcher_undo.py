"""launcher/install.sh --undo against a pretend Fire TV: everything the install changed
goes back.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUARD = "tv.dumbtv.home/tv.dumbtv.home.Guard"


class LauncherUndoTest(unittest.TestCase):
    def undo(self, settings):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            state = tmp / "state.json"
            state.write_text(json.dumps({"packages": {"tv.dumbtv.home": {"system": False, "enabled": True}},
                                         "settings": settings}))
            log = tmp / "commands.log"
            log.touch()
            env = dict(os.environ, ADB=str(ROOT / "tests" / "fake_tv.py"), ADB_SERIAL="test-tv",
                       FAKE_TV_STATE=str(state), FAKE_TV_LOG=str(log))
            result = subprocess.run(["bash", str(ROOT / "launcher" / "install.sh"), "--undo"],
                                    env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return log.read_text().splitlines(), json.loads(state.read_text())["settings"]

    def test_an_earlier_min_futurity_comes_back(self):
        _, settings = self.undo({"global/alarm_manager_constants": "min_futurity=0,other=1",
                                 "global/dumbtv_min_futurity": "5000",
                                 "secure/enabled_accessibility_services": GUARD})
        self.assertEqual(settings["global/alarm_manager_constants"], "other=1,min_futurity=5000")
        self.assertNotIn("global/dumbtv_min_futurity", settings)

    def test_without_an_earlier_value_the_setting_goes(self):
        _, settings = self.undo({"global/alarm_manager_constants": "min_futurity=0",
                                 "secure/enabled_accessibility_services": GUARD})
        self.assertNotIn("global/alarm_manager_constants", settings)

    def test_the_doze_exemption_and_the_preferred_home_go_too(self):
        commands, settings = self.undo({"secure/enabled_accessibility_services": GUARD})
        self.assertIn("dumpsys deviceidle whitelist -tv.dumbtv.home", commands)
        self.assertIn("cmd package clear-package-preferred-activities tv.dumbtv.home", commands)
        self.assertNotIn(GUARD, settings.get("secure/enabled_accessibility_services", ""))


if __name__ == "__main__":
    unittest.main()
