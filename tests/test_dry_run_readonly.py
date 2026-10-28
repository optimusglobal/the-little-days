"""No-render dry run regression tests; all data mocked."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dry_run_readonly import inspect
from production_guard import GuardError

class FakeSheet:
    def __init__(self, config): pass
    def read(self):
        headers=['']*18
        headers[11]='Ảnh tham chiếu'
        headers[12]='Frame 0'
        headers[17]='Trạng thái sản xuất'
        rows=[['']*18 for _ in range(2)]
        rows[0][0]='IDEA_001'
        rows[0][11]='https://drive.google.com/file/d/reference'
        rows[1][0]='IDEA_002'
        rows[1][12]='https://drive.google.com/file/d/frame0'
        rows[1][17]='Bị chặn'
        return {'headers':headers,'rows':rows}

class DryRunTests(unittest.TestCase):
    def test_blocked_idea_never_submits(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'config.json'
            path.write_text(json.dumps({'header_row':4,'headers':{'frame':'Frame 0'}}),encoding='utf8')
            with patch('dry_run_readonly.Sheets',FakeSheet),patch('dry_run_readonly.check_historical_lock',side_effect=GuardError('historical lock')):
                result=inspect('IDEA_002',str(path))
                self.assertEqual(result['historical_lock'],'BLOCK')
                self.assertEqual(result['decision'],'NO_GO')
                self.assertEqual(result['render'],'NEVER_SUBMITTED')
            # Script source contains no submission or ledger-writing calls.
            source=Path('dry_run_readonly.py').read_text(encoding='utf8')
            self.assertNotIn('job.submit(',source)
            self.assertNotIn('reserve_submission(',source)
            self.assertNotIn('record_attempt(',source)

if __name__=='__main__':unittest.main()
