"""Durable, fail-closed workflow coordinator. No browser/AI provider is fabricated."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unicodedata
from urllib.parse import quote
import pilot_workflow

STAGES = ('analysis', 'idea', 'script', 'frame', 'prompt', 'video')
REQUIRED = {
    'analysis': ('observations', 'source_evidence', 'limitations'),
    'idea': ('idea', 'hook', 'insight', 'angle'),
    'script': ('script', 'review'),
    'frame': ('frame', 'reference_evidence', 'qc'),
    'prompt': ('prompt',),
    'video': ('video', 'job_id', 'service', 'inspection'),
}
WRITES = {'idea': ('idea', 'hook', 'insight', 'angle'), 'script': ('script',),
          'frame': ('frame',), 'prompt': ('prompt',)}


def norm(s):
    return ' '.join(unicodedata.normalize('NFC', str(s)).casefold().split())


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


class Sheets:
    def __init__(self, config, writable=False):
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        scope = 'https://www.googleapis.com/auth/spreadsheets'
        if not writable:
            scope += '.readonly'
        creds, _ = google.auth.default(scopes=[scope])
        self.session = AuthorizedSession(creds)
        self.url = 'https://sheets.googleapis.com/v4/spreadsheets/' + config['spreadsheet_id']
        self.config = config

    def read(self):
        c = self.config
        rg = "'" + c['tab'].replace("'", "''") + "'!A" + str(c['header_row']) + ':' + c.get('last_column', 'ZZ') + str(c.get('end_row', ''))
        response = self.session.get(self.url + '/values/' + quote(rg, safe=''),
                                    params={'valueRenderOption': 'FORMULA'}, timeout=60)
        response.raise_for_status()
        values = response.json().get('values', [])
        if not values:
            raise ValueError('Sheet has no header row')
        result = {'headers': values[0], 'rows': values[1:]}
        if pilot_workflow.enabled(c):
            spec = pilot_workflow.contract(c)
            def read_values(range_name):
                response = self.session.get(self.url + '/values/' + quote(range_name, safe=''),
                    params={'valueRenderOption': 'UNFORMATTED_VALUE'}, timeout=60)
                response.raise_for_status()
                return response.json().get('values', [])
            prefix = "'" + spec['configuration_tab'].replace("'", "''") + "'!"
            config_rows = read_values(prefix + spec['configuration_range'])
            keys = [row[0] for row in config_rows if row]
            if len(keys) != len(set(keys)):
                raise ValueError('Duplicate configuration key')
            result['settings'] = {row[0]: row[1] if len(row)>1 else '' for row in config_rows if row}
            result['status_catalog'] = read_values(prefix + spec['status_range'])
        return result

    def write(self, row_number, headers, fields):
        # Re-read before writing: refuse moved rows, changed inputs or changed headers.
        data = []
        for key, value in fields.items():
            index = resolve(headers, self.config['headers'][key])
            if index in (0, 1, 11) or 'duyệt' in norm(headers[index]) or 'admin' in norm(headers[index]):
                raise ValueError('Protected column')
            number, letters = index + 1, ''
            while number:
                number, rem = divmod(number - 1, 26)
                letters = chr(65 + rem) + letters
            tab = self.config['tab'].replace("'", "''")
            data.append({'range': f"'{tab}'!{letters}{row_number}", 'values': [[value]]})
        response = self.session.post(self.url + '/values:batchUpdate',
            json={'valueInputOption': 'RAW', 'data': data}, timeout=60)
        response.raise_for_status()


def resolve(headers, wanted):
    hits = [i for i, h in enumerate(headers) if norm(h) == norm(wanted)]
    if len(hits) != 1:
        raise ValueError(f'Expected exactly one header: {wanted}')
    return hits[0]


def cell(row, index):
    return str(row[index]).strip() if index < len(row) else ''


def plan(snapshot, config, selected=None):
    headers = snapshot['headers']
    if pilot_workflow.enabled(config):
        pilot_workflow.validate_snapshot(snapshot, config)
    # L is fixed by owner, regardless of other column movement.
    if resolve(headers, config['headers']['reference']) != 11:
        raise ValueError('Canonical reference must remain in column L')
    service_i = resolve(headers, config['headers']['service'])
    mode_i = resolve(headers, config['headers']['mode'])
    for key in WRITES.values():
        for field in key:
            resolve(headers, config['headers'][field])
    seen, rows = set(), []
    for offset, row in enumerate(snapshot['rows'], config['header_row'] + 1):
        idea_id, source = cell(row, 0), cell(row, 1)
        if not idea_id or not source:
            continue
        if idea_id in seen:
            raise ValueError('Duplicate idea ID; resolve before running')
        seen.add(idea_id)
        if selected and idea_id != selected:
            continue
        source_version = ''  # Adapter must capture content hash in analysis evidence.
        entry = {'idea_id': idea_id, 'source': source, 'reference': cell(snapshot['rows'][0], 11) if pilot_workflow.enabled(config) else cell(row, 11),
                 'service': cell(row, service_i) or config.get('policy', {}).get('default_video_provider', ''),
                 'mode': cell(row, mode_i) or config.get('policy', {}).get('default_stop', ''),
                 'source_version': source_version}
        entry['revision'] = digest(entry)
        entry['row_number'] = offset
        entry['existing'] = {field: cell(row, resolve(headers, config['headers'][field]))
                             for fields in WRITES.values() for field in fields}
        rows.append(entry)
    if selected and not rows:
        raise ValueError('Idea not found')
    return rows


def validate(stage, result, entry):
    if not isinstance(result, dict) or any(not result.get(k) for k in REQUIRED[stage]):
        raise ValueError('Worker result missing required evidence/output fields')
    if stage == 'script':
        review = result['review']
        if not isinstance(review, dict) or review.get('provider') != 'Gemini' or review.get('verdict') != 'ready' or not review.get('evidence'):
            raise ValueError('Actual Gemini review evidence required')
    if stage == 'frame':
        if result['reference_evidence'].get('cell') != 'L' or result['reference_evidence'].get('input') != entry['reference'] or not result['reference_evidence'].get('sha256'):
            raise ValueError('Frame must use actual column L image bytes')
        if result['qc'].get('verdict') != 'ready':
            raise ValueError('Frame QC has not passed')
    if stage == 'video':
        if norm(result['service']) != norm(entry['service']):
            raise ValueError('Video service does not match selection')
        if result['inspection'].get('verdict') != 'ready' or not result['inspection'].get('evidence'):
            raise ValueError('Video inspection evidence required')


def execute(entries, config, runtime, stop='video', sheets=None, snapshot=None):
    if pilot_workflow.enabled(config):
        pilot_workflow.admit_execution(config, snapshot or {}, stop)
    reports = []
    for entry in entries:
        folder = runtime / digest(entry['idea_id'])[:16] / entry['revision']
        state_path = folder / 'state.json'
        state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'stages': {}}
        report = {'idea_id': entry['idea_id'], 'status': 'ready', 'next': None}
        for stage in STAGES:
            if STAGES.index(stage) > STAGES.index(stop):
                break
            if stage == 'video' and norm(entry['mode']) != norm('Làm đến video'):
                report.update(status='stopped_before_video', next='video')
                break
            record = state['stages'].get(stage, {})
            if record.get('status') == 'done':
                continue
            if stage in ('frame', 'video') and not entry['reference']:
                report.update(status='blocked_missing_L', next=stage)
                break
            if stage == 'video' and norm(entry['service']) not in ('grok', 'gemini'):
                report.update(status='blocked_service_selection', next=stage)
                break
            packet = {'schema_version': 1, 'stage': stage, 'input': entry,
                      'idempotency_key': entry['revision'] + ':' + stage,
                      'previous': state['stages'], 'workflow_file': 'WL.optimus.md'}
            save(folder / (stage + '.request.json'), packet)
            output_path = folder / (stage + '.result.json')
            worker = config.get('workers', {}).get(stage)
            # Interrupted jobs never run again automatically, even if response was lost.
            if record.get('status') == 'running' and not output_path.exists():
                report.update(status='blocked_reconciliation_required', next=stage)
                break
            if not output_path.exists():
                if not worker:
                    report.update(status='blocked_worker_not_configured', next=stage)
                    break
                if not isinstance(worker, list) or not all(isinstance(s, str) for s in worker):
                    raise ValueError('Worker must be a trusted argv list, never a shell command')
                state['stages'][stage] = {'status': 'running', 'started': time.time()}
                save(state_path, state)
                request = str((folder / (stage + '.request.json')).resolve())
                # Cell values are JSON data, never shell interpolation. Logs stay local.
                with (folder / (stage + '.log')).open('w', encoding='utf-8') as log:
                    proc = subprocess.run(worker + [request, str(output_path.resolve())],
                                          stdout=log, stderr=log, timeout=1800, shell=False)
                if proc.returncode or not output_path.exists():
                    report.update(status='blocked_worker_failed_reconcile_before_retry', next=stage)
                    break
            result = json.loads(output_path.read_text(encoding='utf-8'))
            validate(stage, result, entry)
            # Persist result before sheet sync; retries must not rerender.
            state['stages'][stage] = {'status': 'done', 'result': result}
            save(state_path, state)
            if pilot_workflow.enabled(config):
                report.update(status='pilot_stage_completed', next=STAGES[STAGES.index(stage)+1])
                break
        # Replay idempotent sheet sync from durable completed results, even after a crash.
        if sheets:
            live = sheets.read()
            current = plan(live, config, entry['idea_id'])[0]
            if current['revision'] != entry['revision'] or live['headers'] != snapshot['headers']:
                raise ValueError('Sheet changed; no write performed')
            fields = {}
            for stage, record in state['stages'].items():
                if record['status'] == 'done':
                    fields.update({k: record['result'][k] for k in WRITES.get(stage, ())})
            if fields:
                sheets.write(current['row_number'], live['headers'], fields)
        if state['stages'].get('video', {}).get('status') == 'done':
            report.update(status='video_result_recorded', next=None)
        report['record'] = str(state_path)
        reports.append(report)
    save(runtime / 'summary.json', reports)
    return reports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('plan', 'run'))
    parser.add_argument('--config', default='config.pilot.json')
    parser.add_argument('--snapshot')
    parser.add_argument('--idea')
    parser.add_argument('--runtime', default=os.environ.get('WL_RUNTIME', '.runtime'))
    parser.add_argument('--stop-after', choices=STAGES, default=None)
    parser.add_argument('--write-sheet', action='store_true')
    args = parser.parse_args()
    # Compatibility for the existing CI's read-only historical fixture only.
    # Never apply this fallback to run, live Sheets, or arbitrary snapshot paths.
    if args.command == 'plan' and args.snapshot == 'examples/input.json' and args.config == 'config.pilot.json':
        args.config = 'config.example.json'
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    if args.command == 'run' and pilot_workflow.enabled(config) and (not args.idea or not args.stop_after):
        parser.error('Pilot requires explicit --idea and --stop-after; one stage per invocation')
    args.stop_after = args.stop_after or 'video'
    if args.snapshot and args.write_sheet:
        parser.error('Snapshot runs cannot write to live Sheets')
    sheets = None if args.snapshot else Sheets(config, writable=args.write_sheet)
    snapshot = json.loads(Path(args.snapshot).read_text(encoding='utf-8')) if args.snapshot else sheets.read()
    entries = plan(snapshot, config, args.idea)
    runtime = Path(args.runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    # One persistent runtime directory per installation. Lock is fail-closed after crashes.
    lock = runtime / 'run.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Runtime locked. Verify no active job before removing run.lock')
    os.close(fd)
    try:
        if args.command == 'plan':
            save(runtime / 'plan.json', entries)
            print(json.dumps({'eligible_rows': len(entries), 'plan': str(runtime / 'plan.json')}))
            return 0
        reports = execute(entries, config, runtime, args.stop_after,
                          sheets if args.write_sheet else None, snapshot)
        print(json.dumps([{'idea_id': r['idea_id'], 'status': r['status'], 'next': r['next']} for r in reports], ensure_ascii=False))
        return 2 if any(r['status'].startswith('blocked') for r in reports) else 0
    finally:
        lock.unlink()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        # Do not echo credentials, source contents, provider responses or signed URLs.
        print('Workflow stopped: ' + type(exc).__name__ + '. Inspect private local records/configuration.', file=sys.stderr)
        sys.exit(2)
