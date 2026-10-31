"""Synthetic bridge tests only; no private production key or real GitHub approval."""
import base64
import hashlib
import unittest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from approval_guard import canonical
from approval_v3 import FIELDS
from approval_evidence_chain import verify_v3_with_github_evidence
from production_guard import GuardError

class EvidenceChainTests(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        self.commit="b"*40
        self.timeline={"idea_id":"IDEA_BRIDGE_TEST","segments":[{"segment_id":"01","prompt":"8 seconds"}]}
        self.run={"id":5001,"head_sha":self.commit,"status":"completed","conclusion":"success","actor":{"login":"Author"}}
        self.approvals=[{"state":"approved","user":{"login":"Reviewer"},"environments":[{"name":"human-approval"}]}]
        self.rec={"schema_version":3,"decision":"approved","idea_id":"IDEA_BRIDGE_TEST",
            "timeline_sha256":hashlib.sha256(canonical(self.timeline)).hexdigest(),
            "source_commit":self.commit,"review_run_id":"5001","reviewer":"Reviewer",
            "initiator":"Author","review_event_id":"trusted_event","key_id":"fixture"}
    def signed(self):
        record=dict(self.rec)
        record["signature"]=base64.b64encode(self.key.sign(canonical({k:record[k] for k in FIELDS}))).decode()
        return record
    def verify(self, record):
        return verify_v3_with_github_evidence(self.timeline,record,self.public,
            run=self.run,approvals=self.approvals,expected_commit=self.commit,
            trusted_review_event_id="trusted_event")
    def test_chain_valid_synthetic(self):
        self.assertTrue(self.verify(self.signed()))
    def test_forged_github_reviewer_blocked(self):
        record=self.signed();self.approvals[0]["user"]["login"]="Imposter"
        with self.assertRaises(GuardError): self.verify(record)
    def test_github_self_review_blocked(self):
        record=self.signed();self.approvals[0]["user"]["login"]="Author"
        with self.assertRaises(GuardError): self.verify(record)
    def test_github_wrong_actor_blocked(self):
        record=self.signed();self.run["actor"]["login"]="Other"
        with self.assertRaises(GuardError): self.verify(record)
    def test_signed_wrong_run_blocked(self):
        record=self.signed();self.run["id"]=5002
        with self.assertRaises(GuardError): self.verify(record)
    def test_signed_wrong_event_blocked(self):
        record=self.signed()
        with self.assertRaises(GuardError):
            verify_v3_with_github_evidence(self.timeline,record,self.public,
                run=self.run,approvals=self.approvals,expected_commit=self.commit,
                trusted_review_event_id="other_event")

if __name__=="__main__": unittest.main()
