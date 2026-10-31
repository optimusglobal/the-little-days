"""Local Gemini browser execution over Playwright MCP; never handles login secrets.

Run on the same computer as Chrome/Commander. Bind MCP to localhost only.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

class Blocked(RuntimeError):
    pass


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(text):
    return ' '.join(text.replace('\\"', '"').split())


def require_packet(packet, check_assets=True):
    required = ('idea_id', 'source', 'reference_url', 'frame_url', 'prompt', 'service', 'model', 'version')
    if any(not isinstance(packet.get(k), str) or not packet[k].strip() for k in required):
        raise Blocked('Packet missing required input fields')
    if packet['service'].casefold() != 'gemini':
        raise Blocked('Only Gemini browser UI has been verified; Grok is not configured')
    if packet.get('mode') != 'Làm đến video':
        raise Blocked('Row does not request video output')
    if check_assets:
        for field in ('frame', 'reference'):
            path = Path(packet[field + '_path'])
            if not path.is_file() or sha(path) != packet[field + '_sha256']:
                raise Blocked('Asset missing or changed: ' + field)
            with path.open('rb') as stream:
                magic = stream.read(12)
            if not (magic.startswith(b'\x89PNG\r\n\x1a\n') or magic.startswith(b'\xff\xd8')):
                raise Blocked('Expected PNG/JPEG bytes: ' + field)
    # Identity binds to source + reference + actual frame + exact prompt/model/version.
    identity = {k: packet.get(k) for k in required + ('frame_sha256', 'reference_sha256', 'mode')}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@contextmanager
def lock(folder):
    p = folder / 'browser.lock'
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Blocked('Another process is active, or a stale lock needs reconciliation')
    os.close(fd)
    try:
        yield
    finally:
        p.unlink()


class MCP:
    def __init__(self, endpoint='http://localhost:8931/mcp'):
        u = urlsplit(endpoint)
        if u.scheme != 'http' or u.hostname != 'localhost' or u.path != '/mcp':
            raise Blocked('Use localhost MCP endpoint only')
        self.endpoint, self.session, self.counter = endpoint, None, 0
        self.rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
            'clientInfo': {'name': 'LittleDays-browser', 'version': '0.2'}})
        self.rpc('notifications/initialized', notify=True)

    def rpc(self, method, params=None, notify=False):
        self.counter += 1
        body = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notify:
            body['id'] = self.counter
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        req = Request(self.endpoint, data=json.dumps(body).encode(), headers=headers)
        with urlopen(req, timeout=90) as res:
            self.session = res.headers.get('Mcp-Session-Id', self.session)
            if res.status == 202:
                return {}
            if 'text/event-stream' in res.headers.get('Content-Type', ''):
                result = None
                for raw in res:
                    line = raw.decode().strip()
                    if line.startswith('data:'):
                        obj = json.loads(line[5:])
                        if obj.get('id') == self.counter:
                            result = obj
                            break
                if result is None:
                    raise Blocked('Missing MCP response')
            else:
                result = json.loads(res.read())
        if result.get('error'):
            raise Blocked('MCP request failed; no automatic resubmission')
        return result.get('result', {})

    def call(self, name, arguments=None):
        result = self.rpc('tools/call', {'name': name, 'arguments': arguments or {}})
        if result.get('isError'):
            raise Blocked('Browser action failed: ' + name)
        return '\n'.join(p.get('text', '') for p in result.get('content', []) if p.get('type') == 'text')

    def evaluate(self, function):
        text = self.call('browser_evaluate', {'function': function})
        raw = text.split('### Result\n', 1)[-1].split('\n### ', 1)[0].strip()
        return json.loads(raw)

    def click(self, selector):
        return self.call('browser_click', {'target': selector})

    def page(self):
        return self.evaluate('''() => ({url:location.href, title:document.title,
          text:document.body.innerText,
          buttons:Array.from(document.querySelectorAll('button')).map(b=>({text:b.innerText,label:b.getAttribute('aria-label')})),
          videos:Array.from(document.querySelectorAll('video')).map(v=>({duration:Number.isFinite(v.duration)?v.duration:null,width:v.videoWidth,height:v.videoHeight,readyState:v.readyState}))})''')


def require_gemini(page):
    if urlsplit(page['url']).hostname != 'gemini.google.com' or not urlsplit(page['url']).path.startswith('/app'):
        raise Blocked('Select an authorized Gemini /app tab; do not inspect other sites')


def result_state(page, prompt):
    require_gemini(page)
    if canonical(prompt) not in canonical(page['text']):
        raise Blocked('Canonical prompt is not present in this conversation')
    if any(v.get('width', 0) > 0 and v.get('height', 0) > 0 for v in page['videos']):
        return 'video_available'
    lower = page['text'].casefold()
    if 'full capacity' in lower or 'try again later' in lower:
        return 'service_error'
    return 'pending'


def artifact(path):
    path = Path(path)
    with path.open('rb') as f:
        magic = f.read(64)
    if b'ftyp' not in magic:
        raise Blocked('Downloaded file is not an MP4 container')
    return {'path': str(path.resolve()), 'size_bytes': path.stat().st_size, 'sha256': sha(path)}


class Job:
    def __init__(self, packet, root, client):
        self.packet, self.client = packet, client
        self.key = require_packet(packet)
        self.folder = Path(root) / self.key
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / 'browser-state.json'
        self.state = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {
            'idempotency_key': self.key, 'idea_id': packet['idea_id'], 'status': 'new',
            'prompt_sha256': hashlib.sha256(packet['prompt'].encode()).hexdigest(),
            'frame_sha256': packet['frame_sha256'], 'reference_sha256': packet['reference_sha256'],
            'service': 'Gemini', 'model_requested': packet['model'], 'version': packet['version']}

    def save(self, **values):
        self.state.update(values, updated_at=datetime.now().astimezone().isoformat())
        atomic(self.path, self.state)

    def adopt(self, url):
        # Explicit recovery only. No claim that this tool submitted the existing job.
        if self.state['status'] == 'downloaded':
            return
        if self.state['status'] not in ('new', 'pending', 'submission_uncertain', 'submitted', 'video_available'):
            raise Blocked('Reconcile state before adopting a different result')
        parsed = urlsplit(url)
        if parsed.hostname != 'gemini.google.com' or not re.fullmatch(r'/app/[a-zA-Z0-9]+', parsed.path):
            raise Blocked('Expected Gemini conversation URL')
        self.client.call('browser_navigate', {'url': url})
        page = self.client.page()
        status = result_state(page, self.packet['prompt'])
        self.save(status=status, conversation_url=url, job_id=parsed.path.rsplit('/', 1)[-1],
                  origin='adopted_existing', media_metadata=page['videos'],
                  qc='pending', provenance='Existing result; original upload association needs human/AI review')

    def prepare(self):
        if self.state['status'] not in ('new', 'awaiting_extension_file_permission'):
            raise Blocked('Job already exists; resume it instead of making another chat')
        page = self.client.page()
        if urlsplit(page['url']).path != '/app':
            self.client.call('browser_navigate', {'url': 'https://gemini.google.com/app'})
            page = self.client.page()
        require_gemini(page)
        # Find buttons only by actual observed UI labels. Never select approximate models.
        picker = next((b['label'] for b in page['buttons'] if b['label'] and 'chọn chế độ' in b['label']), None)
        if not picker:
            raise Blocked('Model picker missing or login needed')
        if self.packet['model'].casefold() not in picker.casefold():
            self.client.click('button[aria-label=' + json.dumps(picker) + ']')
            raise Blocked('Select the exact requested model in Chrome, then rerun prepare; no prompt submitted')
        # Video mode may require user to select from a changing menu. Detect, do not guess.
        video_mode = any('Bỏ chọn Video' == b['label'] for b in page['buttons'])
        if not video_mode:
            self.client.click('button[aria-label="Nội dung tải lên và công cụ"]')
            self.client.call('browser_snapshot')
            self.client.click('[role="menuitemcheckbox"]:has-text("Tạo video")')
            page = self.client.page()
            if not any(b['label'] == 'Bỏ chọn Video' for b in page['buttons']):
                raise Blocked('Video mode was not selected')
        self.client.call('browser_snapshot')
        self.client.click('button[aria-label^="Tỷ lệ khung hình"]')
        self.client.call('browser_snapshot')
        self.client.click('[role="menuitemradio"]:has-text("Dọc (9:16)")')
        page = self.client.page()
        if not any(b['label'] and '9:16' in b['label'] for b in page['buttons']):
            raise Blocked('9:16 selection was not confirmed')
        self.client.click('button[aria-label="Tải tệp lên"]')
        try:
            self.client.call('browser_file_upload', {'paths': [str(Path(self.packet['frame_path']).resolve())]})
        except Blocked:
            self.save(status='awaiting_extension_file_permission', blocker='Upload failed; check Playwright extension Allow access to file URLs and project roots')
            raise Blocked('Upload blocked. Enable Allow access to file URLs for Playwright Extension in Chrome, then prepare again; no job submitted')
        self.client.call('browser_type', {'target': '[role="textbox"][contenteditable="true"]',
                                          'text': self.packet['prompt'], 'submit': False})
        self.save(status='prepared', opening_url=self.client.page()['url'],
                  upload={'path': self.packet['frame_path'], 'sha256': self.packet['frame_sha256']})

    def submit(self):
        if self.state['status'] != 'prepared':
            raise Blocked('Only a prepared job may submit; interrupted submissions require reconciliation')
        page = self.client.page()
        require_gemini(page)
        model = next((b['label'] for b in page['buttons'] if b['label'] and 'chọn chế độ' in b['label']), '')
        if self.packet['model'].casefold() not in model.casefold():
            raise Blocked('Selected model changed')
        if canonical(self.packet['prompt']) not in canonical(page['text']):
            raise Blocked('Prompt draft is missing')
        # Commit intent BEFORE Enter. If HTTP response is lost, NEVER press Enter again.
        self.save(status='submission_uncertain')
        self.client.call('browser_press_key', {'key': 'Enter'})
        page = self.client.page()
        require_gemini(page)
        path = urlsplit(page['url']).path
        if not re.fullmatch(r'/app/[a-zA-Z0-9]+', path):
            raise Blocked('Submission sent; conversation ID not available yet. Reconcile in Chrome')
        self.save(status='submitted', conversation_url=page['url'], job_id=path.rsplit('/', 1)[-1], origin='submitted_here')

    def poll(self):
        if self.state['status'] == 'downloaded':
            return
        if not self.state.get('conversation_url'):
            raise Blocked('No job URL; inspect Chrome and adopt exact conversation, never resubmit')
        self.client.call('browser_navigate', {'url': self.state['conversation_url']})
        page = self.client.page()
        self.save(status=result_state(page, self.packet['prompt']), media_metadata=page['videos'], qc='pending')

    def download(self, downloads, output):
        if self.state['status'] == 'downloaded':
            artifact(self.state['artifact']['path'])
            return
        if self.state['status'] != 'video_available':
            raise Blocked('No verified available video to download')
        # Only one generated result per conversation is safe for an automatic download.
        page = self.client.page()
        require_gemini(page)
        if urlsplit(page['url']).path != urlsplit(self.state['conversation_url']).path:
            raise Blocked('Current conversation differs from recorded job')
        if len(page['videos']) != 1:
            raise Blocked('Multiple/no videos; select result explicitly before downloading')
        folder = Path(downloads)
        before = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in folder.glob('*.mp4')}
        self.client.call('browser_snapshot')
        self.client.click('button[aria-label="Tải video xuống"]')
        deadline = time.monotonic() + 45
        chosen, last_size, stable = None, None, 0
        while time.monotonic() < deadline:
            files = [p for p in folder.glob('*.mp4')
                     if before.get(str(p)) != (p.stat().st_size, p.stat().st_mtime_ns)]
            if len(files) > 1:
                raise Blocked('Multiple new downloads; do not guess which file is the result')
            if files:
                chosen = files[0]
                size = chosen.stat().st_size
                stable = stable + 1 if size == last_size and size > 0 else 0
                last_size = size
                if stable >= 2 and not chosen.with_suffix(chosen.suffix + '.crdownload').exists():
                    break
            time.sleep(1)
        else:
            raise Blocked('Download not confirmed. Preserve job; do not rerender')
        info = artifact(chosen)
        target = Path(output)
        target.mkdir(parents=True, exist_ok=True)
        # Preserve browser filename; canonical video code has not been assigned by owner.
        destination = target / chosen.name
        if destination.exists() and sha(destination) != info['sha256']:
            raise Blocked('Destination exists with different content')
        if not destination.exists():
            import shutil
            shutil.copy2(chosen, destination)
        self.save(status='downloaded', artifact=artifact(destination), media_metadata=page['videos'],
                  qc='pending', delivery='raw; subtitles and creative QA not yet completed')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('prepare', 'submit', 'poll', 'download', 'adopt'))
    ap.add_argument('--packet', required=True)
    ap.add_argument('--runtime', default=os.environ.get('WL_BROWSER_RUNTIME', '.runtime/browser'))
    ap.add_argument('--endpoint', default='http://localhost:8931/mcp')
    ap.add_argument('--conversation')
    ap.add_argument('--downloads', default=str(Path.home() / 'Downloads'))
    ap.add_argument('--output', default=str(Path.home() / 'Videos' / 'TheLittleDays'))
    args = ap.parse_args()
    packet = json.loads(Path(args.packet).read_text(encoding='utf-8'))
    # Validate before starting any browser action.
    require_packet(packet)
    job = Job(packet, args.runtime, MCP(args.endpoint))
    with lock(job.folder):
        if args.action == 'adopt':
            if not args.conversation:
                raise Blocked('--conversation required')
            job.adopt(args.conversation)
        elif args.action == 'download':
            job.download(args.downloads, args.output)
        elif args.action == 'submit':
            raise Blocked('Direct submission disabled; use run_browser.py --send-confirmed with P0 guards')
        else:
            getattr(job, args.action)()
    print(json.dumps({'idea_id': packet['idea_id'], 'status': job.state['status'],
                      'qc': job.state.get('qc', 'pending'), 'record': str(job.path)}, ensure_ascii=True))

if __name__ == '__main__':
    try:
        main()
    except Blocked as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print('BLOCKED: ' + type(exc).__name__ + '; preserve job state and inspect local logs', file=sys.stderr)
        sys.exit(2)
