"""P0 regression tests, written before production changes. No network, browser, or render."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from production_guard import check_timeline, authorize_submission, record_attempt, GuardError

class ProductionGuardTests(unittest.TestCase):
    def test_script_prompt_duration_conflict(self):
        with self.assertRaises(GuardError):
            check_timeline("One continuous shot. 12 seconds.", "MASTER — 16 seconds. Cut to close-up.")
    def test_unapproved_cut_in_continuous_shot(self):
        with self.assertRaises(GuardError):
            check_timeline("12s, one continuous shot.", "12 seconds. Cut to close-up.")
    def test_dialogue_not_silently_dropped(self):
        with self.assertRaises(GuardError):
            check_timeline('8s. Daughter: "Mama, no." Mother: "No?"',
                           '8 seconds. Daughter: "Mama, no."')
    def test_matching_scene(self):
        check_timeline('12s. One continuous shot. Daughter: "Mama, no."',
                       '12 seconds. Single continuous shot. Daughter says "Mama, no."')
    def test_explicit_authorization_required(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(GuardError):
                authorize_submission(Path(tmp), "IDEA_002", "01", False, False)
    def test_revision_requires_extra_approval_and_budget(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            authorize_submission(root, "IDEA_002", "01", True, False)
            record_attempt(root, "IDEA_002", "01", "key1")
            with self.assertRaises(GuardError):
                authorize_submission(root, "IDEA_002", "01", True, False)
            authorize_submission(root, "IDEA_002", "01", True, True)
            record_attempt(root, "IDEA_002", "01", "key2")
            with self.assertRaises(GuardError):
                authorize_submission(root, "IDEA_002", "01", True, True)
    def test_same_key_cannot_submit_twice(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            record_attempt(root, "IDEA_002", "01", "same-key")
            with self.assertRaises(GuardError):
                record_attempt(root, "IDEA_002", "01", "same-key")

if __name__ == "__main__":
    unittest.main()
