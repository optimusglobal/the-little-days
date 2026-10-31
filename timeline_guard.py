"""P0 deterministic structured storyboard admission (not semantic video QC).

A timeline must be explicitly authored/reviewed. Text matching proves only
contract consistency, never that a generative model will follow the prompt.
"""
import hashlib
import math
import re
from production_guard import GuardError

def _normalize(value):
    return ' '.join(value.split()).casefold()

def _duration(text):
    m = re.search(r'(?i)\b(\d+(?:\.\d+)?)\s*[-‑–]?\s*(?:seconds?|s)\b', text)
    return float(m.group(1)) if m else None

def validate_timeline(packet):
    timeline = packet.get('timeline')
    if not isinstance(timeline, dict) or timeline.get('schema_version') != 1:
        raise GuardError('Approved structured timeline v1 is required')
    script = packet.get('script', '')
    if hashlib.sha256(script.encode('utf-8')).hexdigest() != timeline.get('script_sha256'):
        raise GuardError('Timeline is not bound to this script')
    segments = timeline.get('segments')
    if not isinstance(segments, list) or not segments:
        raise GuardError('Timeline requires at least one segment')
    if len(segments) > 20:
        raise GuardError('Timeline segment count exceeds limit')
    expected_start = 0.0
    identifiers = set()
    chosen = None
    for segment in segments:
        if not isinstance(segment, dict):
            raise GuardError('Invalid segment')
        sid = segment.get('segment_id')
        if not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,24}', sid) or sid in identifiers:
            raise GuardError('Missing or duplicate segment ID')
        identifiers.add(sid)
        start, end = segment.get('start'), segment.get('end')
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end)):
            raise GuardError('Segment requires finite start/end times')
        if abs(start - expected_start) > 0.01 or end <= start:
            raise GuardError('Timeline gap, overlap or nonpositive duration')
        expected_start = float(end)
        if sid == packet.get('segment_id'):
            chosen = segment
    total = timeline.get('total_duration')
    if type(total) not in (int, float) or abs(total - expected_start) > 0.01:
        raise GuardError('Timeline total duration mismatch')
    if chosen is None:
        raise GuardError('Packet segment is not in approved timeline')
    duration = chosen['end'] - chosen['start']
    prompt = packet.get('prompt', '')
    if not isinstance(prompt, str) or not prompt:
        raise GuardError('Segment prompt missing')
    declared_duration = _duration(prompt)
    if declared_duration is None or abs(declared_duration - duration) > 0.05:
        raise GuardError('Segment duration does not match prompt')
    dialogue = chosen.get('dialogue')
    if not isinstance(dialogue, list):
        raise GuardError('Segment dialogue must be an explicit list')
    lines = []
    for turn in dialogue:
        if not isinstance(turn, dict):
            raise GuardError('Invalid dialogue turn')
        speaker, words = turn.get('speaker'), turn.get('text')
        if not isinstance(speaker, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]{0,39}', speaker):
            raise GuardError('Invalid speaker')
        if not isinstance(words, str) or not words.strip():
            raise GuardError('Invalid dialogue text')
        lines.append(f'{speaker}: "{words}"')
    expected = [_normalize(line) for line in lines]
    # Speaker+line must be explicitly attributed, unique and ordered.
    haystack = _normalize(prompt)
    offset = 0
    for line in expected:
        index = haystack.find(line, offset)
        if index < 0:
            raise GuardError('Dialogue missing, reordered or speaker mismatch: ' + line[:64])
        offset = index + len(line)
    found = re.findall(r'([A-Za-z][A-Za-z0-9 _-]{0,39}):\s*["“]([^"”]+)["”]', prompt)
    actual = [_normalize(f'{speaker}: "{words}"') for speaker, words in found]
    if actual != expected:
        raise GuardError('Unexpected, missing or reordered spoken dialogue')
    actions = chosen.get('required_actions')
    if not isinstance(actions, list):
        raise GuardError('Required actions must be an explicit list')
    for action in actions:
        if not isinstance(action, str) or not action.strip() or _normalize(action) not in haystack:
            raise GuardError('Required action missing from prompt')
    return True
