"""Sheet v1.3 contract and pilot admission. No AI/browser calls or credentials."""
import json
from pathlib import Path
from urllib.parse import urlsplit
import re

SCHEMA = 'tld-sheet-v1.3'

def enabled(config):
    return config.get('schema_version') == SCHEMA

def contract(config):
    data = json.loads(Path(config['contract_file']).read_text(encoding='utf-8'))
    if data['schema_version'] != SCHEMA or data['spreadsheet_id'] != config['spreadsheet_id']:
        raise ValueError('Pilot contract identity mismatch')
    return data

def validate_snapshot(snapshot, config):
    spec = contract(config)
    if snapshot['headers'] != spec['headers']:
        raise ValueError('Sheet v1.3 header schema mismatch')
    settings = snapshot.get('settings')
    if not isinstance(settings, dict) or settings.get('schema_version') != SCHEMA:
        raise ValueError('Sheet configuration snapshot required')
    for key in ('deployment_state', 'render_enabled', 'default_stop', 'default_video_provider',
                'max_render_submissions_per_segment', 'max_render_submissions_per_day'):
        if settings.get(key) != config['policy'][key]:
            raise ValueError('Pilot policy differs from live settings: ' + key)
    for key in ('canonical_reference_cell', 'canonical_reference_drive_id', 'canonical_reference_sha256'):
        if settings.get(key) != spec['configuration_snapshot'][key]:
            raise ValueError('Canonical reference configuration mismatch')
    if snapshot.get('status_catalog') != spec['status_catalog']:
        raise ValueError('Production status catalog mismatch')
    reference = snapshot.get('rows', [[]])[0][11] if snapshot.get('rows') and len(snapshot['rows'][0]) > 11 else ''
    u = urlsplit(str(reference))
    m = re.fullmatch(r'/file/d/([A-Za-z0-9_-]+)(?:/.*)?', u.path)
    if u.scheme != 'https' or u.hostname != 'drive.google.com' or not m or m.group(1) != spec['canonical_reference']['drive_id']:
        raise ValueError('L5 canonical Drive reference mismatch')
    # Actual image bytes are checked by the media adapter, not by URL planning.
    return settings

def admit_execution(config, snapshot, stop):
    settings = validate_snapshot(snapshot, config)
    if settings['deployment_state'] != 'ACTIVE':
        raise ValueError('Pilot deployment not activated; plan only')
    if stop == 'video' or settings.get('render_enabled') is not False:
        raise ValueError('Pilot render adapter not commissioned; render remains disabled')
    if settings.get('current_pilot_scope') == 'IDEA_ONLY' and stop not in ('analysis', 'idea'):
        raise ValueError('Pilot currently stops at idea review')
    if not config['policy'].get('step_by_step'):
        raise ValueError('Pilot must execute one incomplete stage per invocation')
    return True

def block_uncommissioned_render(config):
    if enabled(config):
        raise ValueError('Sheet v1.3 render/export adapter not commissioned; no browser side effects')
