"""C.4 production-signing contract tests, using disposable keys only.

No real approval is generated. Tests exercise the existing schema-v2 contract.
"""
import base64
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from approval_guard import canonical, digest, signed_fields, verify_approval
from production_guard import GuardError
from tools.approver_sign_offline import signed_receipt

class ProductionSigningContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for target, value in [('approval_guard.CONTROL_ROOT', self.root / 'control'),
                              ('approval_guard.TRUST_ROOT', self.root / 'trusted')]:
            p = patch(target, value)
            p.start()
            self.addCleanup(p.stop)
        self.key = Ed25519PrivateKey.generate()
        self.private = self.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        (self.root / 'trusted').mkdir()
        (self.root / 'trusted' / 'isolated_test.pem').write_bytes(
            self.key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo))
        self.timeline = {'idea_id': 'IDEA_CONTRACT_TEST', 'schema_version': 1,
                         'segments': [{'segment_id': '01', 'prompt': '8 seconds. Test only.'}]}

    def receipt(self):
        receipt = signed_receipt(self.timeline, 'independent-test-reviewer',
                                 'isolated_test', self.private, digest(self.timeline))
        approvals = self.root / 'control' / 'approvals'
        approvals.mkdir(parents=True, exist_ok=True)
        (approvals / 'IDEA_CONTRACT_TEST.json').write_text(json.dumps(receipt), encoding='utf8')
        return receipt

    def test_independent_signature_verifies(self):
        self.receipt()
        self.assertTrue(verify_approval(self.timeline, 'IDEA_CONTRACT_TEST'))

    def test_wrong_confirmed_digest_rejected(self):
        with self.assertRaises(GuardError):
            signed_receipt(self.timeline, 'reviewer', 'isolated_test', self.private, '0' * 64)

    def test_missing_receipt_fails_closed(self):
        with self.assertRaises(GuardError):
            verify_approval(self.timeline, 'IDEA_CONTRACT_TEST')

    def test_tampered_reviewer_fails(self):
        record = self.receipt()
        record['approved_by'] = 'attacker'
        (self.root / 'control' / 'approvals' / 'IDEA_CONTRACT_TEST.json').write_text(json.dumps(record))
        with self.assertRaises(GuardError):
            verify_approval(self.timeline, 'IDEA_CONTRACT_TEST')

    def test_tampered_key_id_fails(self):
        record = self.receipt()
        record['key_id'] = 'unauthorized'
        (self.root / 'control' / 'approvals' / 'IDEA_CONTRACT_TEST.json').write_text(json.dumps(record))
        with self.assertRaises(GuardError):
            verify_approval(self.timeline, 'IDEA_CONTRACT_TEST')

    def test_untrusted_signer_fails(self):
        record = self.receipt()
        (self.root / 'trusted' / 'isolated_test.pem').unlink()
        with self.assertRaises(GuardError):
            verify_approval(self.timeline, 'IDEA_CONTRACT_TEST')

    def test_timeline_changed_after_signing_fails(self):
        self.receipt()
        self.timeline['segments'][0]['prompt'] = 'Modified'
        with self.assertRaises(GuardError):
            verify_approval(self.timeline, 'IDEA_CONTRACT_TEST')

    def test_approval_flag_is_not_authority(self):
        self.timeline['approval'] = 'approved'
        with self.assertRaises(GuardError):
            signed_receipt(self.timeline, 'reviewer', 'isolated_test', self.private, digest(self.timeline))

if __name__ == '__main__':
    unittest.main()
