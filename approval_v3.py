"""Version-3 approval evidence envelope: verification only, no render authorization.

V3 deliberately uses a separate verifier from legacy v2. A cryptographic
signature authenticates the attestation, but cannot independently prove that
a GitHub reviewer actually approved; production must obtain verified GitHub
review provenance from an independent trusted authority.
"""
import base64
import hashlib
import json
import re
from pathlib import Path

from approval_guard import canonical
from production_guard import GuardError

FIELDS = ("schema_version", "decision", "idea_id", "timeline_sha256",
          "source_commit", "review_run_id", "reviewer", "initiator",
          "review_event_id", "key_id")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SAFE = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")

def verify_v3_attestation(timeline, receipt, trusted_public_key_pem, *,
                          expected_commit, expected_run_id, expected_review_event_id):
    if not isinstance(timeline, dict) or not isinstance(receipt, dict):
        raise GuardError("Invalid timeline or v3 attestation")
    try:
        if set(receipt) != set(FIELDS) | {"signature"}:
            raise GuardError("Unexpected or missing v3 receipt fields")
        if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 3:
            raise GuardError("Unsupported v3 receipt version")
        if receipt["decision"] != "approved":
            raise GuardError("Approval denied")
        idea = timeline.get("idea_id")
        if not isinstance(idea, str) or not SAFE.fullmatch(idea) or receipt["idea_id"] != idea:
            raise GuardError("Idea mismatch")
        sha = hashlib.sha256(canonical(timeline)).hexdigest()
        if not isinstance(receipt["timeline_sha256"], str) or not HEX64.fullmatch(receipt["timeline_sha256"]) or receipt["timeline_sha256"] != sha:
            raise GuardError("Timeline digest mismatch")
        if not isinstance(expected_commit, str) or not HEX40.fullmatch(expected_commit) or receipt["source_commit"] != expected_commit:
            raise GuardError("Commit mismatch")
        if (not isinstance(expected_run_id, str) or not expected_run_id.isdecimal()
                or receipt["review_run_id"] != expected_run_id):
            raise GuardError("Review run mismatch")
        if (not isinstance(expected_review_event_id, str) or not SAFE.fullmatch(expected_review_event_id)
                or receipt["review_event_id"] != expected_review_event_id):
            raise GuardError("Review event mismatch")
        for k in ("reviewer", "initiator", "key_id"):
            if not isinstance(receipt[k], str) or not SAFE.fullmatch(receipt[k]):
                raise GuardError("Invalid v3 identity")
        if receipt["reviewer"].casefold() == receipt["initiator"].casefold():
            raise GuardError("Self-review forbidden")
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = serialization.load_pem_public_key(trusted_public_key_pem)
        if not isinstance(key, Ed25519PublicKey):
            raise GuardError("Wrong key type")
        signature = base64.b64decode(receipt["signature"], validate=True)
        key.verify(signature, canonical({k: receipt[k] for k in FIELDS}))
    except GuardError:
        raise
    except Exception as exc:
        raise GuardError("V3 signature invalid or evidence malformed") from exc
    return True
