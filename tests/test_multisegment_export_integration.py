"""No-network multi-segment exporter integration, production paths remain untouched."""
import hashlib, json, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
import export_browser_packet as exp
from browser_video import Blocked

class FakeSheets:
    status='Sẵn sàng'
    change_after_first=False
    calls=0
    def __init__(self,*args):pass
    def read(self):
        type(self).calls+=1
        headers=['Mã idea nội bộ','Link video gốc','Idea mới','Hook','Insight','Angle','Mã tool','DUYỆT','Hook 2','Kịch bản / Storyboard','ADMIN','Ảnh tham chiếu','Frame 0','Prompt video','AI tạo video','Phiên bản','Chế độ / điểm dừng','Trạng thái sản xuất']
        row=['IDEA_DEMO','source','','','','','','','','16 seconds. Actor: "Hello" Actor: "Hello"','','wrong-row-ref','https://drive.google.com/file/d/frame','MASTER PROMPT','Gemini','v1','Làm đến video',self.status]
        first=['IDEA_ANCHOR','source','','','','','','','','','','https://drive.google.com/file/d/L5']
        if self.change_after_first and self.calls>1:row[13]='CHANGED'
        return {'headers':headers,'rows':[first,row]}
class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        FakeSheets.status='Sẵn sàng';FakeSheets.calls=0;FakeSheets.change_after_first=False
        self.config={'header_row':4,'headers':{'hook':'Hook','insight':'Insight','angle':'Angle','idea':'Idea mới','script':'Kịch bản / Storyboard','reference':'Ảnh tham chiếu','frame':'Frame 0','prompt':'Prompt video','service':'AI tạo video','mode':'Chế độ / điểm dừng'}}
        self.timeline={'idea_id':'IDEA_DEMO','approval':'approved','schema_version':1,'script_sha256':hashlib.sha256('16 seconds. Actor: "Hello" Actor: "Hello"'.encode()).hexdigest(),'master_prompt_sha256':hashlib.sha256(b'MASTER PROMPT').hexdigest(),'total_duration':16,'segments':[{'segment_id':f'0{i}','start':(i-1)*8,'end':i*8,'prompt':f'8 seconds. Actor: "Hello". Action {i}','dialogue':[{'speaker':'Actor','text':'Hello'}],'required_actions':[f'Action {i}']} for i in (1,2)]}
        self.timeline['character_dialogue_contract']={'schema_version':2,'cast':[{'id':'Actor','identity_reference':'L5'}],
            'dialogue_manifest':[{'segment_id':f'0{i}','speaker':'Actor','text':'Hello'} for i in (1,2)]}
        self.timeline['source_dialogue_contract']={'schema_version':1,
            'script_sha256':hashlib.sha256('16 seconds. Actor: "Hello" Actor: "Hello"'.encode()).hexdigest(),
            'source_turns':[{'speaker':'Actor','text':'Hello'},{'speaker':'Actor','text':'Hello'}]}
        (self.root/'timeline.json').write_text(json.dumps(self.timeline))
        (self.root/'config.json').write_text(json.dumps(self.config))
    def run_segment(self,sid):
        argv=['export_browser_packet.py','--idea','IDEA_DEMO','--segment',sid,'--timeline',str(self.root/'timeline.json'),'--config',str(self.root/'config.json'),'--output',str(self.root/'output')]
        def download(session,url,path):
            path.write_bytes(b'\x89PNG\r\n\x1a\nFAKE')
        auth=types.ModuleType('google.auth');auth.default=lambda **kwargs:(object(),None)
        requests=types.ModuleType('google.auth.transport.requests');requests.AuthorizedSession=lambda credentials:object()
        transport=types.ModuleType('google.auth.transport');transport.requests=requests
        google=types.ModuleType('google');google.auth=auth;auth.transport=transport
        with patch.object(sys,'argv',argv),patch.dict(sys.modules,{'google':google,'google.auth':auth,'google.auth.transport':transport,'google.auth.transport.requests':requests}),patch.object(exp,'Sheets',FakeSheets),patch.object(exp,'verify_approval',return_value=True),patch.object(exp,'download_image',side_effect=download),patch.object(exp,'require_packet',return_value='fake'):
            exp.main()
        return next((self.root/'output').rglob(f'{sid}/packet.json'))
    def test_two_segments_isolated_and_L5_identical(self):
        a=json.loads(self.run_segment('01').read_text());b=json.loads(self.run_segment('02').read_text())
        self.assertNotEqual(a['prompt'],b['prompt'])
        self.assertEqual(a['reference_url'],'https://drive.google.com/file/d/L5')
        self.assertEqual(a['reference_sha256'],b['reference_sha256'])
        self.assertNotEqual(a['segment_id'],b['segment_id'])
        self.assertEqual(len(list((self.root/'output').rglob('packet.json'))),2)
    def test_held_idea_blocks_before_download(self):
        FakeSheets.status='Bị chặn'
        with self.assertRaisesRegex(Blocked,'not explicitly ready'):self.run_segment('01')
        self.assertEqual(len(list((self.root/'output').rglob('*.png'))),0)
    def test_changed_sheet_blocks_packet_write(self):
        FakeSheets.change_after_first=True
        with self.assertRaisesRegex(Blocked,'Row changed'):self.run_segment('01')
        self.assertEqual(len(list((self.root/'output').rglob('packet.json'))),0)
if __name__=='__main__':unittest.main()
