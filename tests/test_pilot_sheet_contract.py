"""Offline pilot integration: no AI, credentials, browser, or live Sheet writes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import runner
import pilot_workflow
from export_browser_packet import verify_packet_live

class PilotSheetTests(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(Path('config.pilot.json').read_text(encoding='utf-8'))
        self.s = json.loads(Path('examples/pilot.input.json').read_text(encoding='utf-8'))
    def add_idea(self, ident='IDEA_TEST'):
        row=['']*32
        row[0:2]=[ident,'https://example.invalid/source.mp4']
        self.s['rows'].append(row)
    def test_empty_sheet_only_reference_has_zero_jobs(self):
        self.assertEqual(runner.plan(self.s,self.c),[])
    def test_row6_inherits_L5_and_stop_default(self):
        self.add_idea()
        e=runner.plan(self.s,self.c)[0]
        self.assertEqual(e['reference'],self.s['rows'][0][11])
        self.assertEqual(e['row_number'],6)
        self.assertEqual(e['mode'],'Dừng trước render')
    def test_wrong_canonical_reference_blocks(self):
        self.s['rows'][0][11]='https://drive.google.com/file/d/wrong/view'
        with self.assertRaisesRegex(ValueError,'L5'):runner.plan(self.s,self.c)
    def test_header_drift_blocks(self):
        self.s['headers'][13]='Prompt video'
        with self.assertRaisesRegex(ValueError,'schema'):runner.plan(self.s,self.c)
    def test_changed_policy_is_not_silently_activated(self):
        self.s['settings']['render_enabled']=True
        with self.assertRaisesRegex(ValueError,'policy'):runner.plan(self.s,self.c)
    def test_status_catalog_drift_blocks(self):
        self.s['status_catalog'][0][0]='changed'
        with self.assertRaisesRegex(ValueError,'catalog'):runner.plan(self.s,self.c)
    def test_disabled_run_has_zero_worker_calls_and_writes(self):
        self.add_idea()
        e=runner.plan(self.s,self.c)
        with tempfile.TemporaryDirectory() as td, patch('runner.subprocess.run') as worker:
            with self.assertRaisesRegex(ValueError,'not activated'):
                runner.execute(e,self.c,Path(td),stop='analysis',snapshot=self.s)
            worker.assert_not_called()
            self.assertEqual(list(Path(td).iterdir()),[])
    def test_render_export_blocks_before_google_or_browser(self):
        with patch('export_browser_packet.Sheets') as sheets:
            with self.assertRaisesRegex(ValueError,'not commissioned'):
                verify_packet_live({'idea_id':'IDEA_TEST'})
            sheets.assert_not_called()
    def test_duplicate_idea_still_blocks(self):
        self.add_idea();self.add_idea()
        with self.assertRaisesRegex(ValueError,'Duplicate'):runner.plan(self.s,self.c)
    def test_one_incomplete_stage_only_when_explicitly_activated(self):
        # In-memory activation is a test fixture, never a deployment edit.
        self.c['policy']['deployment_state']='ACTIVE'
        self.s['settings']['deployment_state']='ACTIVE'
        self.add_idea()
        e=runner.plan(self.s,self.c)
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/runner.digest(e[0]['idea_id'])[:16]/e[0]['revision']
            runner.save(folder/'analysis.result.json',{'observations':'fixture',
                        'source_evidence':{'fixture':True},'limitations':'offline fixture'})
            reports=runner.execute(e,self.c,Path(td),stop='idea',snapshot=self.s)
            self.assertEqual(reports[0]['status'],'pilot_stage_completed')
            self.assertEqual(reports[0]['next'],'idea')
            self.assertFalse((folder/'idea.request.json').exists())

if __name__=='__main__':unittest.main()
