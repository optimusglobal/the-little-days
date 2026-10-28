"""Deterministic v2 cast and full-dialogue manifest checks (not semantic video QC).

A v2 manifest binds explicit speaker IDs and the complete ordered list of
dialogue turns to their approved segments. No heuristic extraction from an
unstructured script is claimed.
"""
import re
from production_guard import GuardError
from timeline_guard import _normalize

def validate_character_dialogue(packet):
    timeline=packet.get('timeline',{})
    contract=timeline.get('character_dialogue_contract')
    if not isinstance(contract,dict) or contract.get('schema_version')!=2:
        raise GuardError('Character/dialogue contract v2 required')
    cast=contract.get('cast')
    if not isinstance(cast,list) or not cast or len(cast)>20:
        raise GuardError('Explicit cast required')
    speakers=set()
    for c in cast:
        if not isinstance(c,dict) or set(c)!={'id','identity_reference'}:
            raise GuardError('Invalid cast entry')
        sid=c['id']
        if not isinstance(sid,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',sid) or sid in speakers:
            raise GuardError('Duplicate or invalid cast ID')
        speakers.add(sid)
        if c['identity_reference']!='L5':
            raise GuardError('Every character must bind to L5')
    manifest=contract.get('dialogue_manifest')
    if not isinstance(manifest,list):
        raise GuardError('Explicit full dialogue manifest required')
    segments=timeline.get('segments',[])
    expected=[]
    for segment in segments:
        sid=segment.get('segment_id')
        for turn in segment.get('dialogue',[]):
            if turn.get('speaker') not in speakers:
                raise GuardError('Dialogue references unknown cast member')
            expected.append({'segment_id':sid,'speaker':turn['speaker'],'text':turn['text']})
    if len(manifest)!=len(expected):
        raise GuardError('Dialogue omitted or extra across segments')
    for actual,declared in zip(expected,manifest):
        if not isinstance(declared,dict) or set(declared)!={'segment_id','speaker','text'}:
            raise GuardError('Invalid dialogue manifest turn')
        if actual['segment_id']!=declared['segment_id'] or actual['speaker']!=declared['speaker'] or _normalize(actual['text'])!=_normalize(declared['text']):
            raise GuardError('Dialogue reordered, changed, or assigned to wrong speaker')
    identity=packet.get('reference_url')
    if not isinstance(identity,str) or not identity.strip():
        raise GuardError('Canonical L5 reference missing')
    if packet.get('segment_id') not in [s.get('segment_id') for s in segments]:
        raise GuardError('Unknown segment')
    return True
