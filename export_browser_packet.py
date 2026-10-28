"""Read existing prepared sheet row and fetch its exact L/M Drive image bytes.
Requires Google ADC on the computer running this script, not ChatGPT credentials.
"""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
from browser_video import Blocked, atomic, require_packet, sha
from runner import Sheets, plan, resolve, cell
from timeline_guard import validate_timeline
from approval_guard import verify_approval
import hashlib

def select_segment_prompt(timeline, segment_id, master_prompt):
    if timeline.get('master_prompt_sha256') != hashlib.sha256(master_prompt.encode('utf-8')).hexdigest():
        raise Blocked('Timeline not bound to Sheet master prompt')
    matches = [s for s in timeline.get('segments', []) if isinstance(s, dict) and s.get('segment_id') == segment_id]
    if len(matches) != 1 or not isinstance(matches[0].get('prompt'), str) or not matches[0]['prompt'].strip():
        raise Blocked('Approved segment prompt missing or ambiguous')
    return matches[0]['prompt']



def drive_id(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.hostname != 'drive.google.com':
        raise Blocked('Expected a Google Drive file URL; no arbitrary URL downloads')
    match = re.fullmatch(r'/file/d/([A-Za-z0-9_-]+)(?:/.*)?', u.path)
    ident = match.group(1) if match else parse_qs(u.query).get('id', [''])[0]
    if not re.fullmatch(r'[A-Za-z0-9_-]+', ident):
        raise Blocked('Invalid Drive image ID')
    return ident


def download_image(session, url, path):
    ident = drive_id(url)
    with session.get('https://www.googleapis.com/drive/v3/files/' + ident,
                     params={'alt': 'media'}, stream=True, timeout=60) as response:
        response.raise_for_status()
        if not response.headers.get('Content-Type', '').split(';')[0] in ('image/png', 'image/jpeg'):
            raise Blocked('Drive file is not PNG/JPEG')
        total = 0
        tmp = path.with_suffix('.part')
        try:
            with tmp.open('wb') as f:
                for chunk in response.iter_content(65536):
                    total += len(chunk)
                    if total > 25 * 1024 * 1024:
                        raise Blocked('Image exceeds 25 MB')
                    f.write(chunk)
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)



def verify_packet_live(packet, config_path='config.example.json'):
    """Fail closed on stale, altered, or unverifiable live Sheet data."""
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    live = Sheets(config).read()
    entry = plan(live, config, packet['idea_id'])[0]
    row = live['rows'][entry['row_number'] - config['header_row'] - 1]
    expected = {key: cell(row, resolve(live['headers'], config['headers'][key]))
                for key in ('frame', 'prompt', 'service', 'mode', 'script')}
    expected.update(reference=cell(live['rows'][0], 11),
                    production_status=cell(row, resolve(live['headers'], 'Trạng thái sản xuất')),
                    version=cell(row, resolve(live['headers'], 'Phiên bản')),
                    source=entry['source'])
    for key, value in expected.items():
        mapped = 'reference_url' if key == 'reference' else 'frame_url' if key == 'frame' else 'master_prompt' if key == 'prompt' else key
        if packet.get(mapped) != value:
            raise Blocked('Packet differs from current Sheet: ' + key)
    if expected['production_status'] != 'Sẵn sàng':
        raise Blocked('Production status is not explicitly ready')
    require_packet(packet)
    verify_approval(packet.get('timeline'), packet['idea_id'])
    if packet.get('prompt') != select_segment_prompt(packet['timeline'], packet['segment_id'], expected['prompt']):
        raise Blocked('Selected segment prompt differs from approved timeline')
    validate_timeline(packet)
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--idea', required=True)
    ap.add_argument('--config', default='config.example.json')
    ap.add_argument('--model', default='Argon')
    ap.add_argument('--timeline', required=True, help='Preapproved timeline JSON; never auto-author creative content')
    ap.add_argument('--segment', required=True, help='Explicit approved segment ID')
    ap.add_argument('--output', default='.runtime/packets')
    args = ap.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    timeline = json.loads(Path(args.timeline).read_text(encoding='utf-8'))
    verify_approval(timeline, args.idea)
    sheet = Sheets(config)
    live = sheet.read()
    entry = plan(live, config, args.idea)[0]
    row = live['rows'][entry['row_number'] - config['header_row'] - 1]
    fields = {key: cell(row, resolve(live['headers'], config['headers'][key]))
              for key in ('frame', 'prompt', 'reference', 'service', 'mode', 'script')}
    # L5 is the one canonical character identity image for every row.
    fields['reference'] = cell(live['rows'][0], 11)
    status_index = resolve(live['headers'], 'Trạng thái sản xuất')
    production_status = cell(row, status_index)
    if not fields['frame'] or not fields['prompt'] or not fields['reference'] or not fields['script']:
        raise Blocked('Source-to-Frame0 production is not complete; do not invent missing assets')
    # Hash of data, never idea ID as a filesystem component.
    import hashlib
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,24}', args.segment):
        raise Blocked('Invalid segment ID')
    folder = (Path(args.output).resolve() / hashlib.sha256(args.idea.encode()).hexdigest()[:16]
              / args.segment)
    folder.mkdir(parents=True, exist_ok=True)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
    session = AuthorizedSession(creds)
    for field in ('frame', 'reference'):
        download_image(session, fields[field], folder / (field + '.png'))
    version_header = 'Phiên bản'
    version = cell(row, resolve(live['headers'], version_header))
    segment_prompt = select_segment_prompt(timeline, args.segment, fields['prompt'])
    packet = {'idea_id': entry['idea_id'], 'source': entry['source'],
              'frame_url': fields['frame'], 'reference_url': fields['reference'],
              'prompt': segment_prompt, 'master_prompt': fields['prompt'], 'script': fields['script'], 'service': fields['service'], 'mode': fields['mode'],
              'model': args.model, 'version': version, 'segment_id': args.segment, 'production_status': production_status,
              'timeline': timeline}
    for field in ('frame', 'reference'):
        packet[field + '_path'] = str(folder / (field + '.png'))
        packet[field + '_sha256'] = sha(packet[field + '_path'])
    require_packet(packet)
    validate_timeline(packet)
    # Re-read to avoid binding new sheet prompt to stale downloaded assets.
    current = sheet.read()
    current_entry = plan(current, config, args.idea)[0]
    current_row = current['rows'][current_entry['row_number'] - config['header_row'] - 1]
    current_fields = {key: cell(current_row, resolve(current['headers'], config['headers'][key]))
                      for key in fields}
    current_fields['reference'] = cell(current['rows'][0], 11)
    if cell(current_row, resolve(current['headers'], 'Trạng thái sản xuất')) != production_status:
        raise Blocked('Production status changed during export')
    if current['headers'] != live['headers'] or current_entry != entry or current_fields != fields:
        raise Blocked('Row changed during export; rerun before any submission')
    atomic(folder / 'packet.json', packet)
    print(json.dumps({'packet': str(folder / 'packet.json'), 'status': 'exported'}, ensure_ascii=True))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('BLOCKED: ' + type(exc).__name__ + '; check credentials, sharing, headers and prepared assets')
        raise SystemExit(2)
