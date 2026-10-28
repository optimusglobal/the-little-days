"""P0 integration: mocked CLI-to-submit path, no browser, network, or video."""
import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_browser
from browser_video import Blocked
from production_guard import record_attempt

class FakeJob:
    submissions = 0
    def __init__(self, packet, root, client):
        self.packet = packet
        self.key = 'the-packet-key'
        self.folder = Path(root) / 'fake'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / 'fake.json'
        self.state = {'status': 'prepared'}
    def submit(self):
        FakeJob.submissions += 1
        self.state = {'status': 'downloaded', 'artifact': {'path': 'mock.mp4'}}
    def prepare(self):
        raise AssertionError('No preparation expected')
    def download(self,*args):
        raise AssertionError('No download expected')

class CliIntegrationTests(unittest.TestCase):
    def exercise(self, status='Ready', script='12s. Daughter: "Hi"', prompt='12 seconds. Daughter says "Hi"', send=False, uncertain=False, budget=False):
        with tempfile.TemporaryDirectory() as directory:
            packet = {'idea_id':'IDEA_TEST','segment_id':'01','script':script,'prompt':prompt,'production_status':status}
            packet_path=Path(directory)/'packet.json'
            packet_path.write_text(json.dumps(packet,ensure_ascii=False),encoding='utf-8')
            runtime=Path(directory)/'runtime'
            control=Path(directory)/'control'
            control.mkdir()
            (control/'.initialized').write_text('ready',encoding='utf8')
            FakeJob.submissions=0
            if budget:
                record_attempt(control,'IDEA_TEST','01','existing-attempt')
            argv=['run_browser.py','--idea','IDEA_TEST','--packet',str(packet_path),'--runtime',str(runtime)]
            if send: argv.append('--send-confirmed')
            class ScenarioJob(FakeJob):
                def __init__(self,*args):
                    super().__init__(*args)
                    if uncertain: self.state['status']='submission_uncertain'
            with patch('production_guard.CONTROL_ROOT',Path(directory)/'control'),patch('sys.argv',argv),patch('run_browser.Job',ScenarioJob),patch('run_browser.MCP',return_value=object()),patch('run_browser.verify_packet_live',return_value=True),patch('run_browser.verify_approval',return_value=True),patch('run_browser.validate_timeline',side_effect=lambda p: True if p.get('script') and '12 seconds' in p.get('prompt','') else (_ for _ in ()).throw(Blocked('Script and prompt must both be present' if not p.get('script') else 'Segment duration mismatch'))),patch('run_browser.lock',return_value=contextlib.nullcontext()):
                try:
                    run_browser.main()
                    outcome='accepted'
                except Blocked as e:
                    outcome=str(e)
            return outcome,FakeJob.submissions
    def test_blocked_row_never_submits(self):
        outcome,count=self.exercise(status='Bị chặn',send=True)
        self.assertIn('blocked',outcome.lower())
        self.assertEqual(count,0)
    def test_no_explicit_permission_never_submits(self):
        outcome,count=self.exercise(send=False)
        self.assertIn('send-confirmed',outcome)
        self.assertEqual(count,0)
    def test_missing_script_never_submits(self):
        outcome,count=self.exercise(script='',send=True)
        self.assertIn('Script and prompt',outcome)
        self.assertEqual(count,0)
    def test_duration_conflict_never_submits(self):
        outcome,count=self.exercise(prompt='16-second film. Daughter says "Hi"',send=True)
        self.assertIn('duration mismatch',outcome)
        self.assertEqual(count,0)
    def test_uncertain_job_never_submits(self):
        outcome,count=self.exercise(uncertain=True,send=True)
        self.assertIn('uncertain',outcome.lower())
        self.assertEqual(count,0)
    def test_budget_exhausted_without_revision_approval(self):
        outcome,count=self.exercise(send=True,budget=True)
        self.assertIn('revision',outcome.lower())
        self.assertEqual(count,0)
    def test_authorized_job_calls_mock_submit_once(self):
        outcome,count=self.exercise(send=True)
        self.assertEqual(outcome,'accepted')
        self.assertEqual(count,1)

if __name__=='__main__':
    unittest.main()
