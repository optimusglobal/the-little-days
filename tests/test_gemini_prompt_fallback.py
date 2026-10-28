import json
import tempfile
import unittest
from pathlib import Path
from tools.gemini_prompt_fallback import run_fallback

class FallbackTests(unittest.TestCase):
    def test_terminal_503_skips_to_next_model_without_reposting(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);brief=root/"brief.json";brief.write_text("{}")
            out=root/"out";out.mkdir()
            (out/"prompt_00.pending.json").write_text("{}")
            (out/"prompt_00.errors.json").write_text(json.dumps({"errors":[{"http_status":503,"retry_delay_seconds":None}]}))
            (out/"prompt_01.json").write_text(json.dumps({"model":"second"}))
            r=run_fallback(brief,out,["first","second"])
            self.assertEqual(r["status"],"ready")
            self.assertTrue(r["reused"])
    def test_saved_response_blocks_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/"out";out.mkdir()
            (out/"prompt_00.response.json").write_text("{}")
            r=run_fallback(root/"brief",out,["first","second"])
            self.assertEqual(r["status"],"blocked_reconcile_response")
    def test_unknown_pending_blocks_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/"out";out.mkdir()
            (out/"prompt_00.pending.json").write_text("{}")
            r=run_fallback(root/"brief",out,["first","second"])
            self.assertEqual(r["status"],"blocked_pending")
    def test_nonterminal_retry_blocks_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/"out";out.mkdir()
            (out/"prompt_00.pending.json").write_text("{}")
            (out/"prompt_00.errors.json").write_text(json.dumps({"errors":[{"http_status":503,"retry_delay_seconds":10}]}))
            r=run_fallback(root/"brief",out,["first","second"])
            self.assertEqual(r["status"],"blocked_retry_not_terminal")
if __name__=="__main__":unittest.main()
