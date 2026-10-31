import base64
import hashlib
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from approval_guard import canonical
from owner_approval import FIELDS,verify_owner_proof
from production_guard import GuardError

class OwnerProofTests(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        self.timeline={"idea_id":"IDEA_OWNER_TEST","segments":[{"segment_id":"01","prompt":"8s"}]}
        self.commit="a"*40
        self.challenge="b"*64
        self.proof={"schema_version":1,"mode":"single_owner_offline","decision":"approved",
          "idea_id":"IDEA_OWNER_TEST","timeline_sha256":hashlib.sha256(canonical(self.timeline)).hexdigest(),
          "source_commit":self.commit,"challenge":self.challenge,
          "owner_id":"Owner","key_id":"test_fixture"}
    def sign(self):
        p=dict(self.proof)
        p["signature"]=base64.b64encode(self.key.sign(canonical({k:p[k] for k in FIELDS}))).decode()
        return p
    def verify(self,p,used=frozenset()):
        return verify_owner_proof(self.timeline,p,self.pub,source_commit=self.commit,
                 expected_challenge=self.challenge,used_challenges=used)
    def test_valid_test_proof(self): self.assertTrue(self.verify(self.sign()))
    def test_missing_proof(self):
        with self.assertRaises(GuardError): self.verify(None)
    def test_replay_blocked(self):
        with self.assertRaises(GuardError): self.verify(self.sign(),{self.challenge})
    def test_github_self_review_not_enough(self):
        with self.assertRaises(GuardError): self.verify({"github_review":"approved","actor":"Owner"})
    def test_wrong_commit(self):
        p=self.sign();self.commit="c"*40
        with self.assertRaises(GuardError): self.verify(p)
    def test_tamper_timeline(self):
        p=self.sign();self.timeline["segments"][0]["prompt"]="changed"
        with self.assertRaises(GuardError): self.verify(p)
    def test_tamper_signature(self):
        p=self.sign();p["owner_id"]="imposter"
        with self.assertRaises(GuardError): self.verify(p)
    def test_wrong_key(self):
        bad=Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaises(GuardError):
            verify_owner_proof(self.timeline,self.sign(),bad,source_commit=self.commit,
                 expected_challenge=self.challenge,used_challenges=set())
    def test_wrong_challenge(self):
        with self.assertRaises(GuardError):
            verify_owner_proof(self.timeline,self.sign(),self.pub,source_commit=self.commit,
                 expected_challenge="c"*64,used_challenges=set())
    def test_inline_approval_not_enough(self):
        with self.assertRaises(GuardError): self.verify({"approval":"approved"})
if __name__=="__main__":unittest.main()
