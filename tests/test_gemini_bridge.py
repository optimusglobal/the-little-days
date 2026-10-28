import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from adapters.gemini_analysis_idea import execute

class GeminiBridgeTests(unittest.TestCase):
    def test_demo_analysis_refuses_fake_source(self):
        with tempfile.TemporaryDirectory() as d:
            req=Path(d)/"analysis.request.json"
            req.write_text(json.dumps({"stage":"analysis","input":{
                "idea_id":"DEMO_ONLY","source":"https://example.invalid/source.mp4"}}))
            with self.assertRaises(ValueError):
                execute(req,Path(d)/"analysis.result.json")
            self.assertFalse((Path(d)/"analysis.result.json").exists())
    def test_idea_uses_existing_real_evidence_without_api(self):
        with tempfile.TemporaryDirectory() as d:
            final={"idea":"Original idea","hook":"Hook","insight":"Insight","angle":"Angle"}
            review={"verdict":"use","replacement_approved":False,"source_transcript":[],
                    "final_content":final}
            req=Path(d)/"idea.request.json"
            req.write_text(json.dumps({"stage":"idea","previous":{"analysis":{"status":"done",
                "result":{"review_record":{"approved":True,"review":review}}}}}))
            out=Path(d)/"idea.result.json"
            execute(req,out)
            self.assertEqual(json.loads(out.read_text())["idea"],"Original idea")
    def test_idea_cannot_fabricate_gemini_review(self):
        with tempfile.TemporaryDirectory() as d:
            req=Path(d)/"idea.request.json"
            req.write_text(json.dumps({"stage":"idea","previous":{"analysis":{"status":"done",
                "result":{"review_record":{"approved":False,"review":{}}}}}}}))
            with self.assertRaises(ValueError):
                execute(req,Path(d)/"idea.result.json")

if __name__=="__main__":unittest.main()
