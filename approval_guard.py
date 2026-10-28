"""Verify externally signed approval with Ed25519; render has public key only.

Trust store must be provisioned separately from runtime and approvals.
No private signing key is loaded in this module.
"""
import base64
import hashlib
import json
import os
import re
from pathlib import Path
from production_guard import CONTROL_ROOT, GuardError

TRUST_ROOT = Path.home()/'.the-little-days'/'approval-trust'
def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')
def digest(timeline):
    return hashlib.sha256(canonical(timeline)).hexdigest()
def signed_fields(data):
    return {k:data[k] for k in ('schema_version','decision','idea_id','timeline_sha256','approved_by','key_id')}
def verify_approval(timeline,idea):
    if not isinstance(timeline,dict) or timeline.get('idea_id')!=idea:
        raise GuardError('Timeline idea mismatch')
    if not isinstance(idea,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',idea):
        raise GuardError('Invalid idea ID for approval')
    p=CONTROL_ROOT/'approvals'/(idea+'.json')
    if not p.is_file():raise GuardError('Independent timeline approval receipt required')
    try:
        data=json.loads(p.read_text(encoding='utf8'))
        if not isinstance(data,dict) or data.get('schema_version')!=2 or data.get('decision')!='approved' or data.get('idea_id')!=idea:
            raise GuardError('Signed approval receipt required')
        if data.get('timeline_sha256')!=digest(timeline):
            raise GuardError('Timeline changed after approval')
        if not isinstance(data.get('approved_by'),str) or not data['approved_by'].strip():
            raise GuardError('Approval reviewer missing')
        kid=data.get('key_id')
        if not isinstance(kid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',kid):
            raise GuardError('Invalid approval key ID')
        pub=TRUST_ROOT/(kid+'.pem')
        if not pub.is_file():raise GuardError('Trusted approver key missing')
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key=serialization.load_pem_public_key(pub.read_bytes())
        if not isinstance(key,Ed25519PublicKey):raise GuardError('Expected Ed25519 approver key')
        key.verify(base64.b64decode(data['signature'],validate=True),canonical(signed_fields(data)))
    except GuardError:raise
    except Exception as exc:raise GuardError('Approval signature invalid or receipt unreadable') from exc
    return True
