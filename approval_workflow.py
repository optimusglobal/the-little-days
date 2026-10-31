"""Approval review/verification only on the render machine.

Signing runs on a separately controlled approver machine with an Ed25519
private key that must never be copied to Mia, runtime, or GitHub.
"""
import argparse
import json
from pathlib import Path
from approval_guard import digest,verify_approval
from production_guard import GuardError

def load_timeline(path):
    timeline=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(timeline,dict) or not isinstance(timeline.get('idea_id'),str):
        raise GuardError('Timeline missing idea ID')
    return timeline

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['review','verify'])
    parser.add_argument('--timeline',required=True)
    args=parser.parse_args()
    timeline=load_timeline(args.timeline)
    if args.action=='review':
        print(json.dumps({'idea_id':timeline['idea_id'],'timeline_sha256':digest(timeline),
                          'segments':len(timeline.get('segments',[])),
                          'decision':'PENDING_EXTERNAL_APPROVER'},indent=2))
    else:
        verify_approval(timeline,timeline['idea_id'])
        print('SIGNED_APPROVAL_VERIFIED')
if __name__=='__main__':
    try:main()
    except (GuardError,ValueError,OSError):
        print('BLOCKED: approval review or verification failed')
        raise SystemExit(2)
