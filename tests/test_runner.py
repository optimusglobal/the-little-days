import copy
import json
from pathlib import Path
import tempfile
import unittest
import runner

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path('config.example.json').read_text(encoding='utf-8'))
        self.snapshot = json.loads(Path('examples/input.json').read_text(encoding='utf-8'))

    def test_unchecked_admin_is_not_a_gate(self):
        self.assertEqual(len(runner.plan(self.snapshot, self.config)), 1)

    def test_reference_moved_is_blocked(self):
        self.snapshot['headers'][10], self.snapshot['headers'][11] = self.snapshot['headers'][11], self.snapshot['headers'][10]
        with self.assertRaises(ValueError): runner.plan(self.snapshot, self.config)

    def test_duplicate_id_is_blocked(self):
        self.snapshot['rows'] *= 2
        with self.assertRaises(ValueError): runner.plan(self.snapshot, self.config)

    def test_changed_reference_creates_revision(self):
        old = runner.plan(self.snapshot, self.config)[0]
        self.snapshot['rows'][0][11] = 'changed'
        self.assertNotEqual(old['revision'], runner.plan(self.snapshot, self.config)[0]['revision'])

    def test_missing_worker_does_not_fake_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports = runner.execute(runner.plan(self.snapshot, self.config), self.config, Path(tmp))
            self.assertEqual(reports[0]['status'], 'blocked_worker_not_configured')
            state = Path(reports[0]['record'])
            self.assertFalse(state.exists())

    def test_interrupted_job_is_not_resubmitted(self):
        entry = runner.plan(self.snapshot, self.config)[0]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / runner.digest(entry['idea_id'])[:16] / entry['revision']
            runner.save(folder / 'state.json', {'stages': {'analysis': {'status': 'running'}}})
            reports = runner.execute([entry], self.config, Path(tmp))
            self.assertEqual(reports[0]['status'], 'blocked_reconciliation_required')

    def test_resume_skips_completed_analysis(self):
        entry = runner.plan(self.snapshot, self.config)[0]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / runner.digest(entry['idea_id'])[:16] / entry['revision']
            runner.save(folder / 'state.json', {'stages': {'analysis': {'status': 'done', 'result': {}}}})
            reports = runner.execute([entry], self.config, Path(tmp))
            self.assertEqual(reports[0]['next'], 'idea')

    def test_invalid_review_and_frame_rejected(self):
        entry = runner.plan(self.snapshot, self.config)[0]
        with self.assertRaises(ValueError):
            runner.validate('script', {'script': 'x', 'review': {'provider':'ChatGPT','verdict':'ready','evidence':'x'}}, entry)
        with self.assertRaises(ValueError):
            runner.validate('frame', {'frame':'x','reference_evidence':{'cell':'M'},'qc':{'verdict':'ready'}}, entry)

    def test_write_only_outputs_raw_never_admin(self):
        class Response:
            def raise_for_status(self): pass
        class Session:
            def post(s, url, json, timeout):
                self.assertEqual(json['valueInputOption'], 'RAW')
                self.assertEqual([d['range'] for d in json['data']], ["'01_SAN_XUAT'!C5"])
                return Response()
        sheet = object.__new__(runner.Sheets)
        sheet.config, sheet.url, sheet.session = self.config, 'https://unused', Session()
        sheet.write(5, self.snapshot['headers'], {'idea':'=not-a-formula'})

if __name__ == '__main__': unittest.main()
