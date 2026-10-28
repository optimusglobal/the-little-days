"""Source-dialogue and conservative duration tests, no provider calls."""
import copy,hashlib,unittest
from source_dialogue_guard import verify_source_dialogue
from production_guard import GuardError

SCRIPT='Boss: "You are late." Worker: "I live here."'
def packet():
    turns=[{'speaker':'Boss','text':'You are late.'},{'speaker':'Worker','text':'I live here.'}]
    return {'script':SCRIPT,'timeline':{'segments':[
        {'segment_id':'01','start':0,'end':6,'dialogue':[turns[0]]},
        {'segment_id':'02','start':6,'end':12,'dialogue':[turns[1]]}],
      'character_dialogue_contract':{'dialogue_manifest':[
        {'segment_id':'01',**turns[0]},{'segment_id':'02',**turns[1]}]},
      'source_dialogue_contract':{'schema_version':1,'script_sha256':hashlib.sha256(SCRIPT.encode()).hexdigest(),'source_turns':turns}}}
class SourceTests(unittest.TestCase):
    def test_complete_source_passes(self):self.assertTrue(verify_source_dialogue(packet()))
    def test_missing_line_blocked(self):
        p=packet();p['timeline']['source_dialogue_contract']['source_turns'].pop()
        with self.assertRaisesRegex(GuardError,'missing'):verify_source_dialogue(p)
    def test_rewrite_blocked(self):
        p=packet();p['timeline']['source_dialogue_contract']['source_turns'][0]['text']='You were late.'
        with self.assertRaisesRegex(GuardError,'rewritten'):verify_source_dialogue(p)
    def test_wrong_speaker_blocked(self):
        p=packet();p['timeline']['source_dialogue_contract']['source_turns'][0]['speaker']='Worker'
        with self.assertRaisesRegex(GuardError,'reassigned'):verify_source_dialogue(p)
    def test_changed_script_blocked(self):
        p=packet();p['script']='new script'
        with self.assertRaisesRegex(GuardError,'exact script'):verify_source_dialogue(p)
    def test_speech_overload_blocked(self):
        p=packet();p['timeline']['segments'][0]['end']=1
        with self.assertRaisesRegex(GuardError,'Speech exceeds'):verify_source_dialogue(p)
    def test_rate_not_unbounded(self):
        p=packet();p['timeline']['source_dialogue_contract']['max_words_per_minute']=1000
        with self.assertRaisesRegex(GuardError,'speech-rate'):verify_source_dialogue(p)
    def test_no_contract_blocked(self):
        p=packet();p['timeline'].pop('source_dialogue_contract')
        with self.assertRaisesRegex(GuardError,'required'):verify_source_dialogue(p)
if __name__=='__main__':unittest.main()
