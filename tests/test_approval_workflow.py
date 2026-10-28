"""Offline signer tests; private key exists only inside temporary fixture."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from approval_guard import digest,verify_approval
from production_guard import GuardError
from tools.approver_sign_offline import signed_receipt
import json

class ApprovalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.timeline={'idea_id':'IDEA_DEMO','schema_version':1,'segments':[]}
        self.key=Ed25519PrivateKey.generate()
        self.priv=self.key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        (self.root/'trust').mkdir()
        (self.root/'trust'/'fixture.pem').write_bytes(self.key.public_key().public_bytes(
            serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
        for name,value in [('approval_guard.CONTROL_ROOT',self.root),('approval_guard.TRUST_ROOT',self.root/'trust')]:
            p=patch(name,value);p.start();self.addCleanup(p.stop)
    def test_signed_receipt_accepted(self):
        rec=signed_receipt(self.timeline,'reviewer','fixture',self.priv,digest(self.timeline))
        p=self.root/'approvals'/'IDEA_DEMO.json';p.parent.mkdir()
        p.write_text(json.dumps(rec))
        self.assertTrue(verify_approval(self.timeline,'IDEA_DEMO'))
    def test_wrong_digest_blocks_signing(self):
        with self.assertRaisesRegex(GuardError,'digest'):
            signed_receipt(self.timeline,'reviewer','fixture',self.priv,'wrong')
    def test_forged_signature_blocked(self):
        rec=signed_receipt(self.timeline,'reviewer','fixture',self.priv,digest(self.timeline))
        rec['approved_by']='forged'
        p=self.root/'approvals'/'IDEA_DEMO.json';p.parent.mkdir();p.write_text(json.dumps(rec))
        with self.assertRaisesRegex(GuardError,'signature'):
            verify_approval(self.timeline,'IDEA_DEMO')
    def test_old_unsigned_receipt_rejected(self):
        p=self.root/'approvals'/'IDEA_DEMO.json';p.parent.mkdir()
        p.write_text(json.dumps({'schema_version':1,'decision':'approved','idea_id':'IDEA_DEMO',
             'timeline_sha256':digest(self.timeline),'approved_by':'anyone'}))
        with self.assertRaisesRegex(GuardError,'Signed approval'):
            verify_approval(self.timeline,'IDEA_DEMO')
    def test_render_workflow_no_approve_action(self):
        from pathlib import Path
        source=Path('approval_workflow.py').read_text(encoding='utf8')
        self.assertNotIn("choices=['review','approve','verify']",source)
        self.assertNotIn('def approve(',source)
if __name__=='__main__':unittest.main()
