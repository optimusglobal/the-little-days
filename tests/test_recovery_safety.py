"""Recovery cannot authorize or initiate a new render."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_browser
from browser_video import Blocked
class RecoveryTests(unittest.TestCase):
    def run_case(self,conversation,flags=()):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'p.json';p.write_text(json.dumps({'idea_id':'IDEA_TEST','segment_id':'01'}))
            argv=['run_browser.py','--idea','IDEA_TEST','--packet',str(p),'--conversation',conversation,*flags]
            with patch('sys.argv',argv),patch('run_browser.MCP',side_effect=AssertionError('MCP started')) as m:
                with self.assertRaises(Blocked) as e:run_browser.main()
                m.assert_not_called()
                return str(e.exception)
    def test_recovery_rejects_send(self):
        self.assertIn('cannot accept',self.run_case('https://gemini.google.com/app/abc123',['--send-confirmed']))
    def test_recovery_rejects_revision(self):
        self.assertIn('cannot accept',self.run_case('https://gemini.google.com/app/abc123',['--revision-approved']))
    def test_recovery_rejects_host_spoof(self):
        self.assertIn('exact Gemini',self.run_case('https://gemini.google.com.evil.test/app/abc'))
    def test_recovery_rejects_new_chat(self):
        self.assertIn('exact Gemini',self.run_case('https://gemini.google.com/app'))
if __name__=='__main__':unittest.main()
