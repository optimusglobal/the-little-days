"""Durable single-use challenge claims (local test component, not render admission).

Uses exclusive file creation. A claimed challenge remains spent after crashes;
the caller must authenticate and verify proof BEFORE calling claim_challenge.
"""
import os
import re
from pathlib import Path
from production_guard import GuardError

HEX64=re.compile(r"[0-9a-f]{64}\Z")

def claim_challenge(root, challenge):
    if not isinstance(challenge,str) or not HEX64.fullmatch(challenge):
        raise GuardError("Invalid approval challenge")
    location=Path(root)
    if not location.is_dir():
        raise GuardError("Pre-provisioned protected challenge ledger required")
    path=location/(challenge+".spent")
    try:
        fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc:
        raise GuardError("Approval challenge already consumed") from exc
    except OSError as exc:
        raise GuardError("Could not durably claim approval challenge") from exc
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(b"spent\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as exc:
        # Fail closed: do not remove an attempted claim after a write failure.
        raise GuardError("Approval challenge claim failed; manual reconciliation required") from exc
    return True
