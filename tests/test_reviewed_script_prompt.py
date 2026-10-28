import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from adapters.reviewed_script_prompt import execute

class ReviewedHandoffTests(unittest.TestCase):
    def test_missing_script_review_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"request.json"; result=Path(d)/"out.json"
            path.write_text(json.dumps({"stage":"script","input":{"idea_id":"DEMO_ONLY","revision":"test_revision"}}))
            with self.assertRaises(ValueError):
                execute(path,result)
            self.assertFalse(result.exists())
    def test_prompt_requires_frame_and_script_even_with_handoff(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"request.json";result=Path(d)/"out.json"
            path.write_text(json.dumps({"stage":"prompt","input":{"idea_id":"DEMO_ONLY","revision":"test_revision"},"previous":{}}))
            with self.assertRaises(ValueError):
                execute(path,result)
            self.assertFalse(result.exists())
    def test_untrusted_idea_identifier_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"request.json"
            path.write_text(json.dumps({"stage":"script","input":{"idea_id":"../escape","revision":"x"}}))
            with self.assertRaises(ValueError):
                execute(path,Path(d)/"out.json")
if __name__=="__main__":unittest.main()
