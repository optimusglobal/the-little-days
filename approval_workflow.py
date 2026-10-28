"""Operator-only timeline approval. Never auto-approve or submit renders.

Review prints digest; approval requires operator to type exact digest and reviewer.
Receipts are local control records, not cryptographic signatures.
"""
import argparse
import json
import os
from pathlib import Path
from approval_guard import digest, verify_approval
from production_guard import CONTROL_ROOT, GuardError

def load_timeline(path):
    timeline=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(timeline,dict) or not isinstance(timeline.get('idea_id'),str):
        raise GuardError('Timeline missing idea ID')
    return timeline

def approve(timeline, reviewer, typed_digest):
    idea=timeline['idea_id']
    expected=digest(timeline)
    if typed_digest != expected:
        raise GuardError('Typed digest does not match reviewed timeline')
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise GuardError('Human reviewer identity required')
    if timeline.get('approval') not in (None,'pending'):
        raise GuardError('Inline approval flag is not an authority; remove it before review')
    path=CONTROL_ROOT/'approvals'/(idea+'.json')
    # Validate idea before writing outside control directory.
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',idea):
        raise GuardError('Invalid idea ID')
    path.parent.mkdir(parents=True,exist_ok=True)
    receipt={'schema_version':1,'decision':'approved','idea_id':idea,
             'timeline_sha256':expected,'approved_by':reviewer.strip()}
    payload=json.dumps(receipt,sort_keys=True,indent=2)
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise GuardError('Existing approval must be reviewed/revoked separately; never overwrite') from exc
    with os.fdopen(fd,'w',encoding='utf8') as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    verify_approval(timeline,idea)
    return path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['review','approve','verify'])
    parser.add_argument('--timeline',required=True)
    parser.add_argument('--reviewer')
    parser.add_argument('--confirm-sha256')
    args=parser.parse_args()
    timeline=load_timeline(args.timeline)
    sha=digest(timeline)
    if args.action=='review':
        print(json.dumps({'idea_id':timeline['idea_id'],'timeline_sha256':sha,
                          'segments':len(timeline.get('segments',[])),
                          'decision':'PENDING_HUMAN_REVIEW'},indent=2))
    elif args.action=='verify':
        verify_approval(timeline,timeline['idea_id'])
        print('APPROVAL_VERIFIED')
    else:
        if not args.reviewer or not args.confirm_sha256:
            raise GuardError('Approval requires explicit --reviewer and --confirm-sha256')
        approve(timeline,args.reviewer,args.confirm_sha256)
        print('APPROVAL_RECORDED')

if __name__=='__main__':
    try:main()
    except (GuardError,ValueError,OSError) as exc:
        print('BLOCKED: '+type(exc).__name__)
        raise SystemExit(2)
