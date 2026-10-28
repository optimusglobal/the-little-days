"""Deterministic P0 render admission and script/prompt integrity guards."""
import json
import os
from pathlib import Path
import re

class GuardError(RuntimeError):
    pass

def _seconds(text):
    m = re.search(r'(?i)(?:master\s*[—:-]\s*)?(\d+(?:\.\d+)?)\s*[-‑–]?\s*(?:seconds?|s)\b', text)
    return float(m.group(1)) if m else None

def _quotes(text):
    return [re.sub(r'\s+', ' ', x).strip().casefold() for x in re.findall(r'["“]([^"”]+)["”]', text)]

def check_timeline(script, prompt):
    if not script or not prompt:
        raise GuardError('Script and prompt must both be present before render')
    a, b = _seconds(script), _seconds(prompt)
    if a is None or b is None:
        raise GuardError('Unverifiable durations: explicit duration required')
    if abs(a-b)>0.05:
        raise GuardError(f'Script/prompt duration mismatch: {a} vs {b}')
    if re.search(r'(?i)\b(?:one|single)\s+continuous\s+(?:shot|scene)\b', script):
        if re.search(r'(?i)\b(?:cut\s+to|close-up\s+on|hard\s+cut|jump\s+cut)\b', prompt):
            raise GuardError('Unapproved camera cut in continuous shot')
    for quote in _quotes(script):
        if quote not in prompt.casefold():
            raise GuardError('Dialogue missing from prompt: '+quote[:48])
    return True

def check_production_status(status):
    value = str(status or '').casefold().strip()
    if any(label in value for label in ('bị chặn', 'đang chặn', 'tạm dừng', 'on-hold', 'on hold', 'pause')):
        raise GuardError('Production is blocked or on hold')
    return True

def _ledger(root, idea, segment):
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', idea+'_'+segment)
    return Path(root)/'render-ledger'/(safe+'.json')

def _read(root, idea, segment):
    p=_ledger(root,idea,segment)
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else {'attempts':[]}

def check_historical_lock(root, idea):
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', idea)
    marker = Path(root) / 'historical-locks' / (safe + '.json')
    if marker.exists():
        raise GuardError('Historical render reconciliation required; do not submit')
    return True

def authorize_submission(root, idea, segment, confirmed, revision_approved):
    check_historical_lock(root, idea)
    if not confirmed:
        raise GuardError('Explicit send confirmation is required')
    n=len(_read(root,idea,segment)['attempts'])
    if n>=2:
        raise GuardError('Render budget exhausted; human reset required')
    if n>=1 and not revision_approved:
        raise GuardError('Revision render requires separate approval')
    return True

def record_attempt(root, idea, segment, key):
    p = _ledger(root, idea, segment)
    p.parent.mkdir(parents=True, exist_ok=True)
    guard_lock = p.with_suffix('.lock')
    try:
        fd = os.open(guard_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise GuardError('Another submission owns this segment; reconcile first')
    os.close(fd)
    try:
        state = _read(root, idea, segment)
        if any(a['key'] == key for a in state['attempts']):
            raise GuardError('Same render key has already been submitted')
        if len(state['attempts']) >= 2:
            raise GuardError('Render budget exhausted')
        state['attempts'].append({'key':key, 'status':'submission_intent'})
        temp = p.with_suffix('.tmp')
        with temp.open('w', encoding='utf8') as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, p)
        return state
    finally:
        guard_lock.unlink()
