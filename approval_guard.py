"""Fail-closed external timeline approval receipt, independent of packet/runtime.

This is an integrity receipt, not a cryptographic signature: an attacker with
write access to the control directory can replace both timeline and receipt.
"""
import hashlib
import json
import re
from pathlib import Path
from production_guard import CONTROL_ROOT, GuardError

def digest(timeline):
    return hashlib.sha256(json.dumps(timeline,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()

def verify_approval(timeline, idea):
    if not isinstance(timeline,dict) or timeline.get('idea_id')!=idea:
        raise GuardError('Timeline idea mismatch')
    if not isinstance(idea,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',idea):
        raise GuardError('Invalid idea ID for approval')
    receipt=CONTROL_ROOT/'approvals'/(idea+'.json')
    if not receipt.is_file():
        raise GuardError('Independent timeline approval receipt required')
    try:
        data=json.loads(receipt.read_text(encoding='utf8'))
    except (OSError,ValueError) as e:
        raise GuardError('Approval receipt unreadable') from e
    if not isinstance(data,dict) or data.get('schema_version')!=1 or data.get('decision')!='approved' or data.get('idea_id')!=idea:
        raise GuardError('Approval receipt is not valid')
    if data.get('timeline_sha256')!=digest(timeline):
        raise GuardError('Timeline changed after approval')
    if not isinstance(data.get('approved_by'),str) or not data['approved_by'].strip():
        raise GuardError('Approval reviewer missing')
    return True
