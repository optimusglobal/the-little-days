"""Offline structural timeline contract tests; no render or network."""
import copy
import hashlib
import unittest
from timeline_guard import validate_timeline
from production_guard import GuardError

SCRIPT='12s story with 2 segments. Preserve every dialogue beat.'
def packet():
    return {'script':SCRIPT,'segment_id':'01',
            'prompt':'6 seconds. Daughter: "Mama, no." Mother: "No?" Mother kneels near child.',
            'timeline':{'schema_version':1,'script_sha256':hashlib.sha256(SCRIPT.encode()).hexdigest(),
                        'total_duration':12,'segments':[
                            {'segment_id':'01','start':0,'end':6,
                             'dialogue':[{'speaker':'Daughter','text':'Mama, no.'},{'speaker':'Mother','text':'No?'}],
                             'required_actions':['Mother kneels near child']},
                            {'segment_id':'02','start':6,'end':12,
                             'dialogue':[{'speaker':'Father','text':'Me?'}],
                             'required_actions':['Father kneels']}]}}

class TimelineTests(unittest.TestCase):
    def test_good_segment(self):
        self.assertTrue(validate_timeline(packet()))
    def test_different_speaker_is_blocked(self):
        p=packet();p['prompt']=p['prompt'].replace('Mother: "No?"','Father: "No?"')
        with self.assertRaisesRegex(GuardError,'speaker mismatch'):validate_timeline(p)
    def test_missing_dialogue(self):
        p=packet();p['prompt']=p['prompt'].replace('Mother: "No?"','')
        with self.assertRaises(GuardError):validate_timeline(p)
    def test_reordered_dialogue(self):
        p=packet();p['prompt']='6 seconds. Mother: "No?" Daughter: "Mama, no." Mother kneels near child.'
        with self.assertRaises(GuardError):validate_timeline(p)
    def test_extra_dialogue(self):
        p=packet();p['prompt']+=' Father: "Hello"'
        with self.assertRaisesRegex(GuardError,'Unexpected'):validate_timeline(p)
    def test_missing_action(self):
        p=packet();p['prompt']=p['prompt'].replace('Mother kneels near child.','')
        with self.assertRaisesRegex(GuardError,'action'):validate_timeline(p)
    def test_segment_duration_mismatch(self):
        p=packet();p['prompt']=p['prompt'].replace('6 seconds','8 seconds')
        with self.assertRaisesRegex(GuardError,'duration'):validate_timeline(p)
    def test_overlapping_segments(self):
        p=packet();p['timeline']['segments'][1]['start']=5
        with self.assertRaisesRegex(GuardError,'gap, overlap'):validate_timeline(p)
    def test_omitted_total_duration(self):
        p=packet();p['timeline']['total_duration']=8
        with self.assertRaisesRegex(GuardError,'total duration'):validate_timeline(p)
    def test_wrong_script_hash(self):
        p=packet();p['script']='altered'
        with self.assertRaisesRegex(GuardError,'not bound'):validate_timeline(p)
    def test_wrong_segment_selection(self):
        p=packet();p['segment_id']='99'
        with self.assertRaisesRegex(GuardError,'not in approved'):validate_timeline(p)
    def test_missing_schema_fails_closed(self):
        p=packet();del p['timeline']
        with self.assertRaisesRegex(GuardError,'required'):validate_timeline(p)
    def test_valid_second_segment(self):
        p=packet();p['segment_id']='02';p['prompt']='6 seconds. Father: "Me?" Father kneels.'
        self.assertTrue(validate_timeline(p))

if __name__=='__main__':unittest.main()
