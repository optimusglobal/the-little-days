"""Offline full-path integration with real approval, timeline, live packet, and admission guards.

All Google, browser and render interfaces are mocked. All control files are temporary.
"""
import contextlib
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_browser
from approval_guard import digest
from browser_video import Blocked

SCRIPT='12 seconds. Daughter: "Hello"'
PROMPT='12 seconds. Daughter: "Hello". She smiles'
MASTER='Master prompt for 12 seconds'
HEADERS=['Mã idea nội bộ','Link video gốc','Kịch bản / Storyboard','Ảnh tham chiếu','Frame 0','Prompt video','AI tạo video','Chế độ / điểm dừng','Trạng thái sản xuất','Phiên bản']
CONFIG={'header_row':4,'headers':{'script':HEADERS[2],'reference':HEADERS[3],'frame':HEADERS[4],'prompt':HEADERS[5],'service':HEADERS[6],'mode':HEADERS[7]}}
class FakeSheets:
    status='Sẵn sàng'
    master=MASTER
    def __init__(self,*args):pass
    def read(self):
        row=['IDEA_DEMO','source',SCRIPT,'ref','frame',self.master,'Gemini','Làm đến video',self.status,'v1',None,'ref']
        return {'headers':HEADERS,'rows':[row]}
class FakeJob:
    submissions=0
    def __init__(self,packet,root,client):
        self.folder=Path(root)/'fake'
        self.folder.mkdir(parents=True,exist_ok=True)
        self.path=self.folder/'state.json'
        self.key='single-key'
        self.state={'status':'prepared'}
    def submit(self):
        type(self).submissions+=1
        self.state={'status':'downloaded','artifact':{'path':'fake.mp4'}}
    def prepare(self):raise AssertionError('Browser preparation prohibited')
    def download(self,*a):raise AssertionError('Downloads prohibited')

class EndToEndOfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.control=self.root/'control'
        self.control.mkdir()
        (self.control/'.initialized').write_text('ready')
        self.timeline={'schema_version':1,'idea_id':'IDEA_DEMO','approval':'approved',
            'script_sha256':hashlib.sha256(SCRIPT.encode()).hexdigest(),
            'master_prompt_sha256':hashlib.sha256(MASTER.encode()).hexdigest(),
            'total_duration':12,'segments':[{'segment_id':'01','start':0,'end':12,
                        'prompt':PROMPT,'dialogue':[{'speaker':'Daughter','text':'Hello'}],
                        'required_actions':['She smiles']}]}
        self.packet={'idea_id':'IDEA_DEMO','segment_id':'01','script':SCRIPT,'master_prompt':MASTER,
             'prompt':PROMPT,'timeline':self.timeline,'source':'source','frame_url':'frame',
             'reference_url':'ref','service':'Gemini','mode':'Làm đến video',
             'production_status':'Sẵn sàng','version':'v1'}
    def approve(self):
        path=self.control/'approvals'/'IDEA_DEMO.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'schema_version':1,'decision':'approved','idea_id':'IDEA_DEMO',
                  'timeline_sha256':digest(self.timeline),'approved_by':'unit-test-reviewer'}))
    def run_case(self,send=True):
        p=self.root/'packet.json'
        p.write_text(json.dumps(self.packet))
        runtime=self.root/'runtime'
        FakeJob.submissions=0
        argv=['run_browser.py','--idea','IDEA_DEMO','--packet',str(p),
              '--runtime',str(runtime)]
        if send:argv+=['--send-confirmed']
        with patch('sys.argv',argv),patch('export_browser_packet.Sheets',FakeSheets),\
             patch('export_browser_packet.Path.read_text',side_effect=None) if False else contextlib.nullcontext(),\
             patch('export_browser_packet.plan',return_value=[{'row_number':5,'source':'source'}]),\
             patch('export_browser_packet.require_packet',return_value='hash'),\
             patch('export_browser_packet.json.loads',wraps=json.loads),\
             patch('approval_guard.CONTROL_ROOT',self.control),\
             patch('production_guard.CONTROL_ROOT',self.control),\
             patch('run_browser.Job',FakeJob),patch('run_browser.MCP',return_value=object()),\
             patch('run_browser.lock',return_value=contextlib.nullcontext()):
            old=run_browser.verify_packet_live
            # Mock only file config lookup, preserving all actual verifier gates.
            from export_browser_packet import verify_packet_live
            from unittest.mock import mock_open
            real_read=Path.read_text
            def read(path,*a,**kw):
                if str(path)=='config.example.json':return json.dumps(CONFIG)
                return real_read(path,*a,**kw)
            with patch('export_browser_packet.Path.read_text',read):
                try:
                    run_browser.main()
                    return 'ACCEPTED',FakeJob.submissions
                except Exception as exc:
                    return type(exc).__name__+': '+str(exc),FakeJob.submissions
    def test_missing_receipt_stops_submission(self):
        result,count=self.run_case()
        self.assertIn('receipt',result)
        self.assertEqual(count,0)
    def test_matching_approval_allows_one_mock_submission(self):
        self.approve()
        result,count=self.run_case()
        self.assertEqual((result,count),('ACCEPTED',1))
    def test_modified_timeline_stops_submission(self):
        self.approve()
        self.timeline['segments'][0]['prompt']='12 seconds. Daughter: "Hello". She laughs'
        result,count=self.run_case()
        self.assertIn('changed after approval',result)
        self.assertEqual(count,0)
    def test_blocked_sheet_row_stops_submission(self):
        self.approve()
        FakeSheets.status='Bị chặn'
        self.addCleanup(setattr,FakeSheets,'status','Sẵn sàng')
        result,count=self.run_case()
        self.assertIn('production_status',result)
        self.assertEqual(count,0)
    def test_unconfirmed_stops_submission(self):
        self.approve()
        result,count=self.run_case(send=False)
        self.assertIn('send-confirmed',result)
        self.assertEqual(count,0)

if __name__=='__main__':unittest.main()
