"""Keep credentials outside workspace; never print private source data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

secret = os.environ.pop('GOOGLE_SERVICE_ACCOUNT_JSON', '')
if not secret:
    sys.exit('Missing GOOGLE_SERVICE_ACCOUNT_JSON secret. Follow README setup.')
with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / 'credentials.json'
    path.write_text(json.dumps(json.loads(secret)), encoding='utf-8')
    path.chmod(0o600)
    env = dict(os.environ, GOOGLE_APPLICATION_CREDENTIALS=str(path))
    command = [sys.executable, 'runner.py', 'plan', '--config', 'config.pilot.json']
    if os.environ.get('IDEA_ID'):
        command += ['--idea', os.environ['IDEA_ID']]
    sys.exit(subprocess.run(command, env=env, shell=False).returncode)
