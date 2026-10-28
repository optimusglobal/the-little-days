"""Offline independent approval receipt regressions."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from approval_guard import verify_approval,digest
from production_guard import GuardError

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        p=patch('approval_guard.CONTROL_ROOT',self.root)
        p.start()
        self.addCleanup(p.stop)
        self.timeline={'idea_id':'IDEA_TEST','schema_version':1,'segments':[{'segment_id':'01','prompt':'8s'}]}
    def receipt(self, timeline=None, decision='approved'):
        path=self.root/'approvals'/'IDEA_TEST.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'schema_version':1,'decision':decision,'idea_id':'IDEA_TEST',
            'timeline_sha256':digest(timeline or self.timeline),'approved_by':'human-reviewer'}),encoding='utf8')
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
        with self.assertRaisesRegex(GuardError,'not valid'):
            verify_approval(self.timeline,'IDEA_TEST')
    def test_other_idea_blocked(self):
        self.receipt()
        with self.assertRaisesRegex(GuardError,'idea mismatch'):
            verify_approval(self.timeline,'IDEA_OTHER')

if __name__=='__main__':
    unittest.main()
