"""Offline approver-only signer. Run on isolated approver machine, NEVER on Mia.

Requires externally provisioned Ed25519 PEM private key. This program does
not create signing keys or grant approvals; operator must review exact digest
and provide explicit confirmation.
"""
import argparse
import base64
import json
import re
from pathlib import Path
from approval_guard import canonical,digest,signed_fields
from production_guard import GuardError

def signed_receipt(timeline,reviewer,key_id,private_key_pem,confirm_sha256):
    if not isinstance(timeline,dict):raise GuardError('Timeline required')
    idea=timeline.get('idea_id')
    if not isinstance(idea,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',idea):
        raise GuardError('Invalid idea ID')
    if not isinstance(key_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',key_id):
        raise GuardError('Invalid signer ID')
    if not isinstance(reviewer,str) or not reviewer.strip():raise GuardError('Human reviewer required')
    if confirm_sha256!=digest(timeline):raise GuardError('Explicit timeline digest confirmation required')
    if timeline.get('approval')=='approved':raise GuardError('Inline approval is not an authority')
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key=serialization.load_pem_private_key(private_key_pem,password=None)
    if not isinstance(key,Ed25519PrivateKey):raise GuardError('Expected Ed25519 private key')
    receipt={'schema_version':2,'decision':'approved','idea_id':idea,
             'timeline_sha256':confirm_sha256,'approved_by':reviewer.strip(),'key_id':key_id}
    receipt['signature']=base64.b64encode(key.sign(canonical(signed_fields(receipt)))).decode('ascii')
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--timeline',required=True)
    p.add_argument('--key',required=True,help='Private key path on isolated approver machine only')
    p.add_argument('--reviewer',required=True)
    p.add_argument('--key-id',required=True)
    p.add_argument('--confirm-sha256',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    timeline=json.loads(Path(a.timeline).read_text(encoding='utf8'))
    record=signed_receipt(timeline,a.reviewer,a.key_id,Path(a.key).read_bytes(),a.confirm_sha256)
    target=Path(a.output)
    with target.open('x',encoding='utf8') as f:
        json.dump(record,f,ensure_ascii=False,indent=2)
    print('SIGNED_RECEIPT_CREATED_FOR_EXTERNAL_REVIEW')
if __name__=='__main__':main()
