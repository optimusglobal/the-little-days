"""Bind independently verified GitHub review metadata to the signed v3 envelope.

This checks only metadata consistency; an authenticated GitHub audit event
and independent signer remain mandatory for real production authorization.
"""
from approval_v3 import verify_v3_attestation
from github_review_evidence import verify_github_review
from production_guard import GuardError

def verify_v3_with_github_evidence(timeline, receipt, trusted_public_key_pem,
                                   *, run, approvals, expected_commit,
                                   trusted_review_event_id):
    evidence = verify_github_review(run, approvals, expected_commit=expected_commit)
    if receipt.get("reviewer", "").casefold() != evidence["reviewer"].casefold():
        raise GuardError("Signed reviewer differs from GitHub reviewer")
    if receipt.get("initiator", "").casefold() != evidence["initiator"].casefold():
        raise GuardError("Signed initiator differs from GitHub initiator")
    return verify_v3_attestation(
        timeline, receipt, trusted_public_key_pem,
        expected_commit=expected_commit,
        expected_run_id=evidence["run_id"],
        expected_review_event_id=trusted_review_event_id)
