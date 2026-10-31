"""Offline P0 character and full-dialogue integrity regression tests."""
import copy,unittest
from character_dialogue_guard import validate_character_dialogue
from production_guard import GuardError
def packet():
    seg=[{'segment_id':'01','dialogue':[{'speaker':'Boss','text':'You are late.'}]},
         {'segment_id':'02','dialogue':[{'speaker':'Worker','text':'I live here.'}]}]
    return {'reference_url':'https://drive.google.com/file/d/L5','segment_id':'01',
      'timeline':{'segments':seg,'character_dialogue_contract':{'schema_version':2,
        'cast':[{'id':'Boss','identity_reference':'L5'},{'id':'Worker','identity_reference':'L5'}],
        'dialogue_manifest':[{'segment_id':'01','speaker':'Boss','text':'You are late.'},
                            {'segment_id':'02','speaker':'Worker','text':'I live here.'}]}}}
class CharacterDialogueTests(unittest.TestCase):
    def test_exact_complete_manifest_passes(self):self.assertTrue(validate_character_dialogue(packet()))
    def test_missing_last_line_blocks(self):
        p=packet();p['timeline']['character_dialogue_contract']['dialogue_manifest'].pop()
        with self.assertRaisesRegex(GuardError,'omitted'):validate_character_dialogue(p)
    def test_reordered_turns_blocks(self):
        p=packet();m=p['timeline']['character_dialogue_contract']['dialogue_manifest'];m.reverse()
        with self.assertRaisesRegex(GuardError,'reordered'):validate_character_dialogue(p)
    def test_wrong_speaker_blocks(self):
        p=packet();p['timeline']['character_dialogue_contract']['dialogue_manifest'][0]['speaker']='Worker'
        with self.assertRaisesRegex(GuardError,'wrong speaker'):validate_character_dialogue(p)
    def test_wrong_reference_blocks(self):
        p=packet();p['timeline']['character_dialogue_contract']['cast'][1]['identity_reference']='L6'
        with self.assertRaisesRegex(GuardError,'L5'):validate_character_dialogue(p)
    def test_unknown_speaker_blocks(self):
        p=packet();p['timeline']['segments'][1]['dialogue'][0]['speaker']='Stranger'
        with self.assertRaisesRegex(GuardError,'unknown cast'):validate_character_dialogue(p)
    def test_missing_contract_blocks(self):
        p=packet();del p['timeline']['character_dialogue_contract']
        with self.assertRaisesRegex(GuardError,'v2 required'):validate_character_dialogue(p)
if __name__=='__main__':unittest.main()
