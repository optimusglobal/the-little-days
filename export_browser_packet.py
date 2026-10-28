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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--idea', required=True)
    ap.add_argument('--config', default='config.example.json')
    ap.add_argument('--model', default='Argon')
    ap.add_argument('--output', default='.runtime/packets')
    args = ap.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
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
    folder = Path(args.output).resolve() / hashlib.sha256(args.idea.encode()).hexdigest()[:16]
    folder.mkdir(parents=True, exist_ok=True)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
    session = AuthorizedSession(creds)
    for field in ('frame', 'reference'):
        download_image(session, fields[field], folder / (field + '.png'))
    version_header = 'Phiên bản'
    version = cell(row, resolve(live['headers'], version_header))
    packet = {'idea_id': entry['idea_id'], 'source': entry['source'],
              'frame_url': fields['frame'], 'reference_url': fields['reference'],
              'prompt': fields['prompt'], 'script': fields['script'], 'service': fields['service'], 'mode': fields['mode'],
              'model': args.model, 'version': version, 'segment_id': '01', 'production_status': production_status}
    for field in ('frame', 'reference'):
        packet[field + '_path'] = str(folder / (field + '.png'))
        packet[field + '_sha256'] = sha(packet[field + '_path'])
    require_packet(packet)
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
