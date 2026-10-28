"""Offline live-Sheet integrity checks, no Google API."""
import unittest
import hashlib
from export_browser_packet import select_segment_prompt
from unittest.mock import patch
from browser_video import Blocked
from export_browser_packet import verify_packet_live

HEADERS=['Mã idea nội bộ','Link video gốc','Kịch bản / Storyboard','Ảnh tham chiếu','Frame 0','Prompt video','AI tạo video','Chế độ / điểm dừng','Trạng thái sản xuất','Phiên bản']
CONFIG={'header_row':4,'headers':{'script':HEADERS[2],'reference':HEADERS[3],'frame':HEADERS[4],'prompt':HEADERS[5],'service':HEADERS[6],'mode':HEADERS[7]}}
VALUES=['IDEA_X','original','12s','ref','frame','12 seconds','Gemini','Làm đến video','Sẵn sàng','v1',None,'ref']
PACKET={'idea_id':'IDEA_X','source':'original','script':'12s','reference_url':'ref','frame_url':'frame','prompt':'12 seconds','master_prompt':'12 seconds','service':'Gemini','mode':'Làm đến video','production_status':'Sẵn sàng','version':'v1','timeline':{'approval':'approved','idea_id':'IDEA_X','master_prompt_sha256':hashlib.sha256(b'12 seconds').hexdigest(),'segments':[{'segment_id':'01','prompt':'12 seconds'}]},'segment_id':'01'}
class FakeSheet:
    def __init__(self,*args):pass
    def read(self):return {'headers':HEADERS,'rows':[VALUES]}

class PacketFreshnessTests(unittest.TestCase):
    def check(self, packet):
        with patch('export_browser_packet.Path.read_text',return_value='{}'),patch('export_browser_packet.json.loads',return_value=CONFIG),patch('export_browser_packet.Sheets',FakeSheet),patch('export_browser_packet.plan',return_value=[{'row_number':5,'source':'original'}]),patch('export_browser_packet.require_packet',return_value='hash'),patch('export_browser_packet.validate_timeline',return_value=True),patch('export_browser_packet.verify_approval',return_value=True):
            return verify_packet_live(packet)
    def test_exact_live_packet_passes(self):
        self.assertTrue(self.check(dict(PACKET)))
    def test_changed_segment_prompt_blocks(self):
        p=dict(PACKET,prompt='changed')
        with self.assertRaisesRegex(Blocked,'segment prompt'):self.check(p)
    def test_changed_master_prompt_blocks(self):
        p=dict(PACKET,master_prompt='changed')
        with self.assertRaisesRegex(Blocked,'prompt'):self.check(p)
    def test_two_segment_binding(self):
        master='Master 16 seconds with two approved segments'
        timeline={'master_prompt_sha256':hashlib.sha256(master.encode()).hexdigest(),
                  'segments':[{'segment_id':'01','prompt':'8 seconds. Mother: "Hello"'},
                              {'segment_id':'02','prompt':'8 seconds. Father: "Hi"'}]}
        self.assertIn('Mother',select_segment_prompt(timeline,'01',master))
        self.assertIn('Father',select_segment_prompt(timeline,'02',master))
        with self.assertRaisesRegex(Blocked,'master prompt'):select_segment_prompt(timeline,'01',master+' changed')
        with self.assertRaisesRegex(Blocked,'missing'):select_segment_prompt(timeline,'03',master)
    def test_stale_status_blocks(self):
        p=dict(PACKET,production_status='Bị chặn')
        with self.assertRaisesRegex(Blocked,'production_status'):self.check(p)
    def test_changed_frame_blocks(self):
        p=dict(PACKET,frame_url='other')
        with self.assertRaisesRegex(Blocked,'frame'):self.check(p)
    def test_unapproved_timeline_blocks(self):
        p=dict(PACKET,timeline={'approval':'pending','idea_id':'IDEA_X'})
        self.assertTrue(self.check(p))
    def test_foreign_idea_timeline_blocks(self):
        p=dict(PACKET,timeline={'approval':'approved','idea_id':'IDEA_OTHER'})
        with self.assertRaisesRegex(Blocked,'approval'):self.check(p)
    def test_sheet_unavailable_blocks(self):
        with patch('export_browser_packet.Sheets',side_effect=RuntimeError('unavailable')),patch('export_browser_packet.Path.read_text',return_value='{}'):
            with self.assertRaises(Exception):verify_packet_live(dict(PACKET))

if __name__=='__main__':unittest.main()
