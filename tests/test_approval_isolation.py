"""Approval workflow permission-isolation regression tests."""
import tempfile
import unittest
from pathlib import Path
from tools.audit_approval_isolation import ROOT, WORKFLOWS, validate_workflow, audit

class IsolationTests(unittest.TestCase):
    def test_current_workflows(self):
        self.assertEqual({}, audit(ROOT))
    def test_secret_reference_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.yml"
            p.write_text((ROOT / WORKFLOWS[1]).read_text(encoding="utf8") + "\n# ${{ secrets.APPROVAL_SIGNING_KEY }}\n", encoding="utf8")
            self.assertTrue(validate_workflow(p))
    def test_write_permission_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.yml"
            p.write_text((ROOT / WORKFLOWS[1]).read_text(encoding="utf8").replace("contents: read", "contents: write"), encoding="utf8")
            self.assertTrue(validate_workflow(p))
    def test_environment_removed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.yml"
            p.write_text((ROOT / WORKFLOWS[2]).read_text(encoding="utf8").replace("environment: human-approval", ""), encoding="utf8")
            self.assertTrue(validate_workflow(p))
    def test_untrusted_trigger_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.yml"
            p.write_text((ROOT / WORKFLOWS[1]).read_text(encoding="utf8") + "\npull_request_target:\n", encoding="utf8")
            self.assertTrue(validate_workflow(p))

if __name__ == "__main__":
    unittest.main()
