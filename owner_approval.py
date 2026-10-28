"""Single-owner offline authorization proof (test-only verifier).

GitHub self-review is not authorization. Separate owner-held Ed25519 proof
binds one exact timeline, source commit, and random challenge. This verifier
does NOT permit rendering, create keys, or trust arbitrary public keys.
"""
import base64
import hashlib
import re
from approval_guard import canonical
from production_guard import GuardError

FIELDS=("schema_version","mode","decision","idea_id","timeline_sha256",
        "source_commit","challenge","owner_id","key_id")
HEX40=re.compile(r"[0-9a-f]{40}\Z")
HEX64=re.compile(r"[0-9a-f]{64}\Z")
SAFE=re.compile(r"[A-Za-z0-9_-]{1,64}\Z")

def verify_owner_proof(timeline, proof, trusted_pub_pem, *,
                       source_commit, expected_challenge, used_challenges):
    if not isinstance(timeline,dict) or not isinstance(proof,dict):
        raise GuardError("Owner proof required")
    if set(proof)!=set(FIELDS)|{"signature"}:
        raise GuardError("Malformed owner proof")
    if type(proof["schema_version"]) is not int or proof["schema_version"]!=1:
        raise GuardError("Owner proof version invalid")
    if proof["mode"]!="single_owner_offline" or proof["decision"]!="approved":
        raise GuardError("Offline owner authorization missing")
    idea=timeline.get("idea_id")
    if not isinstance(idea,str) or not SAFE.fullmatch(idea) or proof["idea_id"]!=idea:
        raise GuardError("Idea mismatch")
    if not isinstance(source_commit,str) or not HEX40.fullmatch(source_commit) or proof["source_commit"]!=source_commit:
        raise GuardError("Commit mismatch")
    digest=hashlib.sha256(canonical(timeline)).hexdigest()
    if proof["timeline_sha256"]!=digest:
        raise GuardError("Timeline mismatch")
    if not isinstance(expected_challenge,str) or not HEX64.fullmatch(expected_challenge) or proof["challenge"]!=expected_challenge:
        raise GuardError("Challenge mismatch")
    if expected_challenge in used_challenges:
        raise GuardError("Replayed authorization")
    for k in ("owner_id","key_id"):
        if not isinstance(proof[k],str) or not SAFE.fullmatch(proof[k]):
            raise GuardError("Invalid owner identity")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key=serialization.load_pem_public_key(trusted_pub_pem)
        if not isinstance(key,Ed25519PublicKey):
            raise GuardError("Owner key is not Ed25519")
        key.verify(base64.b64decode(proof["signature"],validate=True),
                   canonical({k:proof[k] for k in FIELDS}))
    except GuardError: raise
    except Exception as exc:
        raise GuardError("Owner proof signature invalid") from exc
    return True
