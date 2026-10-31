import json
import tempfile
import unittest
from pathlib import Path
from adapters.gemini_prompt_worker import execute

class PromptWorkerTests(unittest.TestCase):
    def test_rejects_missing_frame(self):
        with tempfile.TemporaryDirectory() as d:
            request=Path(d)/"req.json"
            request.write_text(json.dumps({"stage":"prompt","input":{"idea_id":"IDEA_TEST","revision":"r"},
                                           "previous":{"analysis":{"status":"done"},"idea":{"status":"done"},
                                           "script":{"status":"done"}}}))
            with self.assertRaises(ValueError):
                execute(request,Path(d)/"result.json")
    def test_rejects_wrong_identity_reference(self):
        with tempfile.TemporaryDirectory() as d:
            request=Path(d)/"req.json"
            prior={s:{"status":"done","result":{}} for s in ("analysis","idea","script","frame")}
            prior["frame"]["result"]={"reference_evidence":{"identity_row":6},"qc":{"verdict":"ready"}}
            request.write_text(json.dumps({"stage":"prompt","input":{"idea_id":"IDEA_TEST","revision":"r"},
                                           "previous":prior}))
            with self.assertRaises(ValueError):
                execute(request,Path(d)/"result.json")
if __name__=="__main__":unittest.main()
