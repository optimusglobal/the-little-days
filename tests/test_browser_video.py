import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from browser_video import Blocked, Job, artifact, canonical, require_packet, result_state
from export_browser_packet import drive_id

class BrowserTests(unittest.TestCase):
    def test_grok_not_silently_substituted(self):
        p={k:'x' for k in ('idea_id','source','reference_url','frame_url','prompt','service','model','version')}
        p.update(service='Grok',mode='Làm đến video')
        with self.assertRaises(Blocked): require_packet(p,False)

    def test_prompt_and_video_evidence(self):
        page={'url':'https://gemini.google.com/app/abc','text':'my exact prompt','videos':[{'width':720,'height':1280}]}
        self.assertEqual(result_state(page,'my exact prompt'),'video_available')
        with self.assertRaises(Blocked): result_state(page,'a different prompt')
        page['url']='https://mail.google.com'
        with self.assertRaises(Blocked): result_state(page,'my exact prompt')

    def test_error_does_not_complete_job(self):
        self.assertEqual(result_state({'url':'https://gemini.google.com/app/abc','text':'prompt full capacity','videos':[]},'prompt'),'service_error')

    def test_mp4_required(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fake.mp4'; path.write_text('HTML error')
            with self.assertRaises(Blocked): artifact(path)

    def test_drive_url_validation(self):
        self.assertEqual(drive_id('https://drive.google.com/file/d/abc-123/view'),'abc-123')
        with self.assertRaises(Blocked): drive_id('https://evil.example/image.png')

    def test_escaped_quotes_normalized(self):
        self.assertEqual(canonical('say \\"hi\\"'),canonical('say "hi"'))

    def test_submission_is_single_use_and_intent_is_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            img=Path(temp)/'ref.png'; img.write_bytes(b'\x89PNG\r\n\x1a\nbytes')
            p={k:'x' for k in ('idea_id','source','reference_url','frame_url','prompt','model','version')}
            p.update(service='Gemini',mode='Làm đến video',model='Argon',prompt='exact')
            for field in ('frame','reference'):
                p[field+'_path']=str(img); p[field+'_sha256']=hashlib.sha256(img.read_bytes()).hexdigest()
            class Client:
                def page(self):
                    return {'url':'https://gemini.google.com/app','text':'exact','buttons':[{'label':'chọn chế độ Argon'}]}
                def call(self,*a): raise TimeoutError('lost response')
            job=Job(p,Path(temp)/'state',Client()); job.save(status='prepared')
            with self.assertRaises(TimeoutError): job.submit()
            self.assertEqual(json.loads(job.path.read_text())['status'],'submission_uncertain')
            with self.assertRaises(Blocked): job.submit()

if __name__=='__main__': unittest.main()
