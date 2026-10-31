"""Read-only layout preflight for the user-approved M5 layout; no legacy imports."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
import re

def validate(snapshot, contract, idea):
    if snapshot.get('spreadsheet_id') != contract['spreadsheet_id']:
        raise ValueError('Wrong spreadsheet')
    if snapshot.get('headers') != contract['headers']:
        raise ValueError('Headers changed; explicit layout migration required')
    settings = snapshot.get('settings', {})
    ref = contract['canonical_reference']
    if settings.get('canonical_reference_cell') != contract['tab'] + '!' + ref['cell']:
        raise ValueError('Canonical reference location mismatch')
    for setting, field in [('canonical_reference_drive_id', 'drive_id'),
                           ('canonical_reference_sha256', 'sha256')]:
        if settings.get(setting) != ref[field]:
            raise ValueError('Canonical reference identity mismatch')
    rows = snapshot.get('rows', [])
    if not rows:
        raise ValueError('Missing canonical row')
    row = rows[0]
    if len(row) <= ref['column_index']:
        raise ValueError('Missing M5')
    url = urlsplit(str(row[ref['column_index']]))
    match = re.fullmatch(r'/file/d/([A-Za-z0-9_-]+)(?:/view)?/?', url.path)
    if url.scheme != 'https' or url.hostname != 'drive.google.com' or not match or match[1] != ref['drive_id']:
        raise ValueError('M5 must reference the canonical Drive file')
    populated = [r for r in rows if r and str(r[0]).strip()]
    ids = [str(r[0]).strip() for r in populated]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate idea IDs')
    matches = [r for r in populated if str(r[0]).strip() == idea]
    if len(matches) != 1:
        raise ValueError('Idea not found')
    target = matches[0]
    if len(target) < 2 or not str(target[1]).strip():
        raise ValueError('Missing source URL')
    def value(index):
        return target[index] if len(target) > index else ''
    return {
        'idea_id': idea, 'layout': 'PASS', 'reference_cell': ref['cell'],
        'gpt_idea_present': bool(str(value(2)).strip()),
        'gemini_idea_present': bool(str(value(3)).strip()),
        'media_verified': False, 'review_verified': False,
        'production_ready': False,
        'next_action': 'VERIFY_SOURCE_MEDIA_AND_ACTUAL_GEMINI_CONNECTION'
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot', required=True)
    p.add_argument('--contract', default=str(Path(__file__).with_name('layout.contract.json')))
    p.add_argument('--idea', required=True)
    args = p.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding='utf-8'))
    print(json.dumps(validate(read(args.snapshot), read(args.contract), args.idea),
                     ensure_ascii=False))

if __name__ == '__main__':
    main()
