"""Fail-closed owner approval redemption; not a production render permit.

Verify an offline owner signature before durably consuming its one-use challenge.
A successful redemption is an audit event, NOT authorization to render.
"""
from pathlib import Path
from owner_approval import verify_owner_proof
from owner_challenge_ledger import claim_challenge
from production_guard import GuardError

def redeem_owner_proof(timeline, proof, trusted_public_key_pem, *,
                       source_commit, expected_challenge, protected_ledger):
    ledger = Path(protected_ledger)
    if not ledger.is_dir() or ledger.is_symlink():
        raise GuardError("Protected challenge ledger unavailable")
    # Replay protection is enforced atomically by O_EXCL in claim_challenge.
    verify_owner_proof(timeline, proof, trusted_public_key_pem,
                       source_commit=source_commit,
                       expected_challenge=expected_challenge,
                       used_challenges=frozenset())
    claim_challenge(ledger, expected_challenge)
    return {"verified": True, "challenge_consumed": True,
            "render_authorized": False}
