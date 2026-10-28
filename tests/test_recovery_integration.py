"""Offline crash recovery and exclusive-lock regression coverage; no browser or network."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from browser_video import Blocked, Job, lock, require_packet
from production_guard import record_attempt, GuardError

def packet(tmp):
    img=Path(tmp)/'image.png';img.write_bytes(b'\x89PNG\r\n\x1a\nmock')
    p={k:'x' for k in ('idea_id','source','reference_url','frame_url','prompt','model','version')}
    p.update(service='Gemini',mode='Làm đến video',model='Argon',prompt='exact prompt')
    for kind in ('frame','reference'):
        p[kind+'_path']=str(img)
        p[kind+'_sha256']=hashlib.sha256(img.read_bytes()).hexdigest()
    return p

class Client:
    def __init__(self):
        self.enters=0
    def page(self):
        return {'url':'https://gemini.google.com/app','text':'exact prompt','buttons':[{'label':'chọn chế độ Argon'}]}
    def call(self,name,arguments=None):
        if name=='browser_press_key':
            self.enters+=1
            raise TimeoutError('simulated network loss after Enter')

class RecoveryTests(unittest.TestCase):
    def test_lost_submit_persists_and_restart_never_resubmits(self):
        with tempfile.TemporaryDirectory() as t:
            p=packet(t);c=Client();j=Job(p,Path(t)/'state',c)
            j.save(status='prepared')
            with self.assertRaises(TimeoutError):j.submit()
            self.assertEqual(c.enters,1)
            resumed=Job(p,Path(t)/'state',c)
            self.assertEqual(resumed.state['status'],'submission_uncertain')
            with self.assertRaises(Blocked):resumed.submit()
            self.assertEqual(c.enters,1)

    def test_downloaded_state_survives_restart(self):
        with tempfile.TemporaryDirectory() as t:
            p=packet(t);j=Job(p,Path(t)/'state',Client())
            j.save(status='downloaded',artifact={'path':'mock.mp4'})
            again=Job(p,Path(t)/'state',Client())
            self.assertEqual(again.state['status'],'downloaded')
            with self.assertRaises(Blocked):again.submit()

    def test_two_workers_same_folder_one_lock(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)
            with lock(folder):
                with self.assertRaises(Blocked): 
                    with lock(folder): pass
            with lock(folder):pass

    def test_attempt_replay_stays_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            record_attempt(root,'IDEA_X','01','key-A')
            with self.assertRaises(GuardError):record_attempt(root,'IDEA_X','01','key-A')
            ledger=root/'render-ledger'/'IDEA_X_01.json'
            self.assertEqual(len(json.loads(ledger.read_text())['attempts']),1)

    def test_concurrent_segment_ledger_lock_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder=root/'render-ledger';folder.mkdir()
            guard=folder/'IDEA_X_01.lock'
            guard.write_text('owned',encoding='utf8')
            with self.assertRaisesRegex(GuardError,'Another submission'):
                record_attempt(root,'IDEA_X','01','key-A')

if __name__=='__main__':unittest.main()
