"""GPT/Gemini idea separation regression tests; no live services."""
import json
from pathlib import Path
import unittest
import runner

class IdeaSeparationTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads(Path('config.pilot.json').read_text(encoding='utf-8'))
        self.s=json.loads(Path('examples/pilot.input.json').read_text(encoding='utf-8'))
        self.row=['']*32
        self.row[0:4]=['IDEA_TEST','https://example.invalid/source','GPT draft','']
        self.s['rows'].append(self.row)
    def test_gpt_draft_is_review_input_and_changes_revision(self):
        first=runner.plan(self.s,self.c)[0]
        self.assertEqual(first['gpt_idea'],'GPT draft')
        self.row[2]='Revised GPT draft'
        self.assertNotEqual(first['revision'],runner.plan(self.s,self.c)[0]['revision'])
    def test_gemini_output_writes_D_and_hook_AF_not_GPT_C(self):
        class Response:
            def raise_for_status(self):pass
        sent=[]
        class Session:
            def post(self,url,json,timeout):
                sent.extend(d['range'] for d in json['data'])
                return Response()
        sheet=object.__new__(runner.Sheets)
        sheet.config,selfurl,sheet.session=self.c,'https://unused',Session()
        sheet.url=selfurl
        sheet.write(6,self.s['headers'],{'idea':'Gemini text','hook':'Hook'})
        self.assertEqual(sent,["'01_SAN_XUAT'!D6","'01_SAN_XUAT'!AF6"])
    def test_review_must_have_actual_provider_evidence(self):
        entry=runner.plan(self.s,self.c)[0]
        result={'idea':'rewrite','hook':'hook','insight':'insight','angle':'angle'}
        with self.assertRaisesRegex(ValueError,'Actual Gemini'):runner.validate('idea',result,entry)
        result['review']={'provider':'Gemini','verdict':'revise','evidence':'fixture','response_id':'offline-fixture'}
        runner.validate('idea',result,entry)
    def test_scope_stops_before_script_even_if_activated(self):
        self.c['policy']['deployment_state']='ACTIVE'
        self.s['settings']['deployment_state']='ACTIVE'
        import pilot_workflow
        with self.assertRaisesRegex(ValueError,'stops at idea'):
            pilot_workflow.admit_execution(self.c,self.s,'script')

if __name__=='__main__':unittest.main()
