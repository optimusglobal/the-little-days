"""Only ephemeral keys for tests; NEVER use these keys for production."""
import base64
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from approval_guard import digest,canonical,signed_fields

def make_signed(root,idea,timeline,decision='approved'):
    key=Ed25519PrivateKey.generate()
    trust=root/'trust'
    trust.mkdir(parents=True,exist_ok=True)
    (trust/'fixture.pem').write_bytes(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo))
    receipt={'schema_version':2,'decision':decision,'idea_id':idea,
             'timeline_sha256':digest(timeline),'approved_by':'fixture-reviewer','key_id':'fixture'}
    receipt['signature']=base64.b64encode(key.sign(canonical(signed_fields(receipt)))).decode()
    p=root/'approvals'/(idea+'.json')
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(receipt),encoding='utf8')
    return p
