"""P0-03.4: source-anchored dialogue coverage and conservative speech-time admission.

Source dialogue must be independently transcribed/reviewed against the source script.
A hash binds the source-script bytes; this check cannot semantically extract lines.
"""
import hashlib
import math
import re
from production_guard import GuardError

def verify_source_dialogue(packet):
    timeline=packet.get('timeline',{})
    contract=timeline.get('source_dialogue_contract')
    if not isinstance(contract,dict) or contract.get('schema_version')!=1:
        raise GuardError('Source dialogue contract v1 required')
    script=packet.get('script')
    if not isinstance(script,str) or contract.get('script_sha256')!=hashlib.sha256(script.encode('utf8')).hexdigest():
        raise GuardError('Source dialogue not bound to exact script')
    turns=contract.get('source_turns')
    if not isinstance(turns,list):
        raise GuardError('Reviewed source dialogue list required')
    manifest=timeline.get('character_dialogue_contract',{}).get('dialogue_manifest')
    if not isinstance(manifest,list) or len(turns)!=len(manifest):
        raise GuardError('Source dialogue missing or extra in segments')
    for source, rendered in zip(turns,manifest):
        if not isinstance(source,dict) or set(source)!={'speaker','text'}:
            raise GuardError('Invalid source dialogue turn')
        if source['speaker']!=rendered.get('speaker') or source['text']!=rendered.get('text'):
            raise GuardError('Source dialogue rewritten, reordered or reassigned')
    rate=contract.get('max_words_per_minute',150)
    if type(rate) not in (int,float) or not math.isfinite(rate) or not 60<=rate<=180:
        raise GuardError('Unsafe speech-rate configuration')
    pause=contract.get('pause_seconds_per_turn',0.3)
    if type(pause) not in (int,float) or not math.isfinite(pause) or not 0<=pause<=2:
        raise GuardError('Unsafe pause configuration')
    for segment in timeline.get('segments',[]):
        lines=segment.get('dialogue',[])
        words=sum(len(re.findall(r"\b[\w']+\b",t['text'])) for t in lines)
        minimum=words*60/rate+len(lines)*pause
        if minimum>segment['end']-segment['start']+0.01:
            raise GuardError('Speech exceeds segment duration; extend or split, never truncate dialogue')
    return True
