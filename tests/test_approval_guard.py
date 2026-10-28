"""Offline independent approval receipt regressions."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from approval_guard import verify_approval,digest
from signed_fixture import make_signed
from production_guard import GuardError

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        p=patch('approval_guard.CONTROL_ROOT',self.root)
        p.start()
        self.addCleanup(p.stop)
        trust=patch('approval_guard.TRUST_ROOT',self.root/'trust')
        trust.start()
        self.addCleanup(trust.stop)
        self.timeline={'idea_id':'IDEA_TEST','schema_version':1,'segments':[{'segment_id':'01','prompt':'8s'}]}
    def receipt(self, timeline=None, decision='approved'):
        make_signed(self.root,'IDEA_TEST',timeline or self.timeline,decision)
    def test_missing_receipt_blocked(self):
        with self.assertRaisesRegex(GuardError,'receipt required'):
            verify_approval(self.timeline,'IDEA_TEST')
    def test_separate_matching_receipt_passes(self):
        self.receipt()
        self.assertTrue(verify_approval(self.timeline,'IDEA_TEST'))
    def test_forged_approved_field_does_not_bypass(self):
        t=dict(self.timeline,approval='approved')
        with self.assertRaises(GuardError):
            verify_approval(t,'IDEA_TEST')
    def test_modified_timeline_blocked(self):
        self.receipt()
        self.timeline['segments'][0]['prompt']='changed'
        with self.assertRaisesRegex(GuardError,'changed after'):
            verify_approval(self.timeline,'IDEA_TEST')
    def test_rejected_receipt_blocked(self):
        self.receipt(decision='rejected')
        with self.assertRaisesRegex(GuardError,'Signed approval'):
            verify_approval(self.timeline,'IDEA_TEST')
    def test_other_idea_blocked(self):
        self.receipt()
        with self.assertRaisesRegex(GuardError,'idea mismatch'):
            verify_approval(self.timeline,'IDEA_OTHER')

if __name__=='__main__':
    unittest.main()
