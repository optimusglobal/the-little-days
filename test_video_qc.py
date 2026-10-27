import unittest
from gemini_video_qc import approved
class QCContract(unittest.TestCase):
 def base(self):return {'verdict':'ready','actual_transcript':[],'expected_lines_present':True,'speaker_assignments_correct':True,'material_errors':[],'extra_dialogue':[]}
 def test_ready(self):self.assertTrue(approved(self.base()))
 def test_extra_words_block(self):self.assertFalse(approved(dict(self.base(),extra_dialogue=['Me?'])))
 def test_wrong_parent_blocks(self):self.assertFalse(approved(dict(self.base(),material_errors=['hugged father'])))
 def test_wrong_speaker_blocks(self):self.assertFalse(approved(dict(self.base(),speaker_assignments_correct=False)))
 def test_missing_line_blocks(self):self.assertFalse(approved(dict(self.base(),expected_lines_present=False)))
if __name__=='__main__':unittest.main()
