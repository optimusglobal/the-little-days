"""Issue short-lived owner challenges to a pre-provisioned ledger.

This is a test-only component; no signing keys and no render authority.
"""
import json
import os
import secrets
import time
from pathlib import Path
from production_guard import GuardError

def issue_challenge(ledger, *, now=None, ttl_seconds=300):
    root=Path(ledger)
    if not root.is_dir() or root.is_symlink():
        raise GuardError("Protected challenge ledger unavailable")
    if not isinstance(ttl_seconds,int) or isinstance(ttl_seconds,bool) or not 30<=ttl_seconds<=900:
        raise GuardError("Invalid challenge lifetime")
    current=int(time.time() if now is None else now)
    challenge=secrets.token_hex(32)
    record={"challenge":challenge,"issued_at":current,"expires_at":current+ttl_seconds}
    path=root/(challenge+".issued")
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf8") as handle:
            json.dump(record,handle,sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise GuardError("Challenge issuance failed") from exc
    return record

def validate_issued_challenge(ledger, challenge, *, now=None):
    root=Path(ledger)
    if not root.is_dir() or root.is_symlink():
        raise GuardError("Protected challenge ledger unavailable")
    if not isinstance(challenge,str) or len(challenge)!=64 or any(c not in "0123456789abcdef" for c in challenge):
        raise GuardError("Malformed challenge")
    path=root/(challenge+".issued")
    try:
        if path.is_symlink():
            raise GuardError("Unsafe challenge record")
        record=json.loads(path.read_text(encoding="utf8"))
    except (OSError,ValueError) as exc:
        raise GuardError("Challenge issuance record missing") from exc
    if not isinstance(record,dict) or set(record)!={"challenge","issued_at","expires_at"} or record["challenge"]!=challenge:
        raise GuardError("Invalid challenge issuance record")
    issued=record["issued_at"]; expires=record["expires_at"]
    current=int(time.time() if now is None else now)
    if type(issued) is not int or type(expires) is not int or not 30<=expires-issued<=900 or current<issued or current>=expires:
        raise GuardError("Challenge expired or not yet valid")
    return True
