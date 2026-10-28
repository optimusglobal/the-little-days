"""Only ephemeral keys; v3 cannot grant production rendering."""
import base64
import hashlib
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from approval_guard import canonical
from approval_v3 import FIELDS, verify_v3_attestation
from production_guard import GuardError

class V3EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.timeline={"idea_id":"IDEA_TEST_V3","segments":[{"segment_id":"01","prompt":"8 seconds"}]}
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        self.commit="a"*40
        self.run="123456"
        self.event="approval_event_123"
        self.record=dict(schema_version=3,decision="approved",idea_id="IDEA_TEST_V3",
            timeline_sha256=hashlib.sha256(canonical(self.timeline)).hexdigest(),
            source_commit=self.commit,review_run_id=self.run,reviewer="ReviewerB",
            initiator="CommitterA",review_event_id=self.event,key_id="ephemeral_fixture")
    def sign(self):
        r=dict(self.record)
        r["signature"]=base64.b64encode(self.key.sign(canonical({k:r[k] for k in FIELDS}))).decode()
        return r
    def verify(self,r):
        return verify_v3_attestation(self.timeline,r,self.public,expected_commit=self.commit,
            expected_run_id=self.run,expected_review_event_id=self.event)
    def test_valid_cryptographic_envelope(self):
        self.assertTrue(self.verify(self.sign()))
    def test_modified_commit_fails(self):
        r=self.sign();r["source_commit"]="b"*40
        with self.assertRaises(GuardError): self.verify(r)
    def test_modified_review_fails(self):
        r=self.sign();r["review_event_id"]="other"
        with self.assertRaises(GuardError): self.verify(r)
    def test_changed_timeline_fails(self):
        r=self.sign();self.timeline["segments"][0]["prompt"]="changed"
        with self.assertRaises(GuardError): self.verify(r)
    def test_forged_signer_fails(self):
        r=self.sign();r["reviewer"]="OtherReviewer"
        with self.assertRaises(GuardError): self.verify(r)
    def test_self_review_fails(self):
        self.record["reviewer"]="CommitterA"
        with self.assertRaises(GuardError): self.verify(self.sign())
    def test_wrong_expected_commit_fails(self):
        r=self.sign();self.commit="b"*40
        with self.assertRaises(GuardError): self.verify(r)
    def test_missing_event_fails(self):
        r=self.sign();del r["review_event_id"]
        with self.assertRaises(GuardError): self.verify(r)
    def test_wrong_key_fails(self):
        other=Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaises(GuardError):
            verify_v3_attestation(self.timeline,self.sign(),other,expected_commit=self.commit,expected_run_id=self.run,expected_review_event_id=self.event)

if __name__=="__main__": unittest.main()
