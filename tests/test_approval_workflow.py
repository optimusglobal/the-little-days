"""Approval workflow tests use a temporary external control root; no real approval."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from approval_guard import digest, verify_approval
from approval_workflow import approve
from production_guard import GuardError

class ApprovalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.patch=patch('approval_workflow.CONTROL_ROOT',Path(self.temp.name))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.verify_patch=patch('approval_guard.CONTROL_ROOT',Path(self.temp.name))
        self.verify_patch.start()
        self.addCleanup(self.verify_patch.stop)
        self.timeline={'idea_id':'IDEA_DEMO','schema_version':1,'segments':[]}
    def test_no_confirmation_blocks(self):
        with self.assertRaises(GuardError):
            approve(self.timeline,'reviewer','incorrect')
        self.assertFalse((Path(self.temp.name)/'approvals'/'IDEA_DEMO.json').exists())
    def test_explicit_human_receipt_then_verify(self):
        p=approve(self.timeline,'reviewer',digest(self.timeline))
        self.assertTrue(p.exists())
        self.assertTrue(verify_approval(self.timeline,'IDEA_DEMO'))
    def test_no_silent_overwrite(self):
        approve(self.timeline,'reviewer',digest(self.timeline))
        with self.assertRaisesRegex(GuardError,'never overwrite'):
            approve(self.timeline,'reviewer',digest(self.timeline))
    def test_inline_approved_flag_blocks(self):
        self.timeline['approval']='approved'
        with self.assertRaises(GuardError):
            approve(self.timeline,'reviewer',digest(self.timeline))
    def test_path_traversal_rejected(self):
        self.timeline['idea_id']='../escape'
        with self.assertRaises(GuardError):
            approve(self.timeline,'reviewer',digest(self.timeline))

if __name__=='__main__':unittest.main()
