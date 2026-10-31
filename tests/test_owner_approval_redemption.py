import base64
import hashlib
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from approval_guard import canonical
from owner_approval import FIELDS
from owner_approval_redemption import redeem_owner_proof
from production_guard import GuardError

class OwnerRedemptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger=Path(self.temp.name)
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        self.timeline={"idea_id":"IDEA_REDEEM_TEST","segments":[{"segment_id":"01","prompt":"8s"}]}
        self.commit="a"*40
        self.challenge="b"*64
    def receipt(self):
        r={"schema_version":1,"mode":"single_owner_offline","decision":"approved",
           "idea_id":"IDEA_REDEEM_TEST",
           "timeline_sha256":hashlib.sha256(canonical(self.timeline)).hexdigest(),
           "source_commit":self.commit,"challenge":self.challenge,
           "owner_id":"Owner","key_id":"fixture"}
        r["signature"]=base64.b64encode(self.key.sign(canonical({k:r[k] for k in FIELDS}))).decode()
        return r
    def redeem(self, receipt):
        return redeem_owner_proof(self.timeline,receipt,self.pub,source_commit=self.commit,
                                  expected_challenge=self.challenge,protected_ledger=self.ledger)
    def test_valid_claim_not_render_authority(self):
        self.assertEqual(False,self.redeem(self.receipt())["render_authorized"])
    def test_second_claim_rejected(self):
        r=self.receipt();self.redeem(r)
        with self.assertRaises(GuardError):self.redeem(r)
    def test_invalid_signature_does_not_consume(self):
        r=self.receipt();r["owner_id"]="imposter"
        with self.assertRaises(GuardError):self.redeem(r)
        self.assertFalse((self.ledger/(self.challenge+".spent")).exists())
    def test_concurrent_claim_only_one_succeeds(self):
        r=self.receipt()
        def attempt(_):
            try:self.redeem(r);return True
            except GuardError:return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(attempt,range(16)))
        self.assertEqual(1,sum(results))
    def test_missing_ledger_rejected(self):
        self.ledger=self.ledger/"not-created"
        with self.assertRaises(GuardError):self.redeem(self.receipt())
if __name__=="__main__":unittest.main()
