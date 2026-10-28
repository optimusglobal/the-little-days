import json
import tempfile
import unittest
from pathlib import Path
from adapters.gemini_script_worker import execute

class GeminiScriptWorkerTests(unittest.TestCase):
 def test_missing_analysis_blocks_without_api(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"req.json";p.write_text(json.dumps({"stage":"script","input":{"idea_id":"IDEA_002"},"previous":{}}))
   with self.assertRaises(ValueError):execute(p,Path(d)/"result.json")
 def test_missing_source_transcript_blocks_without_api(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"req.json"
   p.write_text(json.dumps({"stage":"script","input":{"idea_id":"IDEA_002"},"previous":{
    "analysis":{"status":"done","result":{"observations":{"source_transcript":[]}}},
    "idea":{"status":"done","result":{"idea":"x","hook":"x","insight":"x","angle":"x"}}}}))
   with self.assertRaises(ValueError):execute(p,Path(d)/"result.json")
if __name__=="__main__":unittest.main()
