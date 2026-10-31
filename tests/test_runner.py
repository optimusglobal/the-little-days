import json
import tempfile
import unittest
from pathlib import Path
import runner

class V13RunnerTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(Path("config.example.json").read_text(encoding="utf-8"))
        self.snapshot=json.loads(Path("examples/input.json").read_text(encoding="utf-8"))
        self.entry=runner.plan(self.snapshot,self.config)[0]

    def test_live_schema_and_m5(self):
        self.assertEqual(self.entry["reference"],self.snapshot["rows"][0][12])
        self.assertEqual(self.config["spreadsheet_id"],"1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM")

    def test_missing_m5_fail_closed(self):
        self.snapshot["rows"][0][12]=""
        with self.assertRaises(ValueError):runner.plan(self.snapshot,self.config)

    def test_duplicate_id_blocked(self):
        self.snapshot["rows"].append(self.snapshot["rows"][0].copy())
        with self.assertRaises(ValueError):runner.plan(self.snapshot,self.config)

    def test_owner_approval_does_not_reset_revision(self):
        rev=self.entry["revision"]
        self.snapshot["rows"][0][8]="TRUE"
        new=runner.plan(self.snapshot,self.config)[0]
        self.assertEqual(rev,new["revision"])
        self.assertTrue(new["idea_approved"])

    def test_worker_absence_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=runner.execute([self.entry],self.config,Path(tmp))
            self.assertEqual(r[0]["status"],"blocked_worker_not_configured")
            self.assertEqual(r[0]["next"],"analysis")

    def test_missing_gemini_provider_evidence(self):
        with self.assertRaises(ValueError):
            runner.validate("gemini_review",{"idea_gemini":"x","critique":["weak"],"review_evidence":{"provider":"GPT","model":"fake","response_record":"fake"}},self.entry)

    def test_quality_gate_gpt_wins(self):
        obj={"scores":{"gpt":{"total":90,"hard_constraints_pass":True},"gemini":{"total":87,"hard_constraints_pass":True}},"selected":"gpt","verdict":"ready","rationale":"clearer punchline"}
        runner.validate("quality_gate",obj,self.entry)

    def test_quality_gate_gemini_wins(self):
        obj={"scores":{"gpt":{"total":84,"hard_constraints_pass":True},"gemini":{"total":92,"hard_constraints_pass":True}},"selected":"gemini","verdict":"ready","rationale":"stronger acting"}
        runner.validate("quality_gate",obj,self.entry)

    def test_quality_gate_neither(self):
        obj={"scores":{"gpt":{"total":65,"hard_constraints_pass":True},"gemini":{"total":72,"hard_constraints_pass":True}},"selected":"none","verdict":"revise","rationale":"weak hook"}
        runner.validate("quality_gate",obj,self.entry)

    def test_quality_gate_rejects_failing_hard_constraint(self):
        obj={"scores":{"gpt":{"total":99,"hard_constraints_pass":False},"gemini":{"total":70,"hard_constraints_pass":True}},"selected":"gpt","verdict":"ready","rationale":"invalid"}
        with self.assertRaises(ValueError):runner.validate("quality_gate",obj,self.entry)

    def test_owner_approval_needed_before_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/runner.digest(self.entry["idea_id"])[:16]/self.entry["revision"]
            scores={"gpt":{"total":91,"hard_constraints_pass":True},"gemini":{"total":85,"hard_constraints_pass":True}}
            stages={
                "analysis":{"status":"done","result":{"observations":"seen","source_evidence":"video","limitations":"none"}},
                "gpt_idea":{"status":"done","result":{"idea_gpt":"a"}},
                "gemini_review":{"status":"done","result":{"idea_gemini":"b","critique":["shorter hook"],"review_evidence":{"provider":"Gemini","model":"mock","response_record":"stored"}}},
                "quality_gate":{"status":"done","result":{"scores":scores,"selected":"gpt","verdict":"ready","rationale":"best"}}}
            runner.save(folder/"state.json",{"stages":stages})
            out=runner.execute([self.entry],self.config,Path(tmp))
            self.assertEqual(out[0]["status"],"blocked_awaiting_owner_approval")

    def test_protected_admin_and_identity_columns(self):
        class S:
            def post(self,*a,**k):raise AssertionError("must not send")
        sh=object.__new__(runner.Sheets)
        sh.config=self.config;sh.url="https://unused";sh.session=S()
        for key in ("reference",):
            with self.assertRaises(ValueError):sh.write(5,self.snapshot["headers"],{key:"changed"})

    def test_v13_output_only_writes_candidate(self):
        class R:
            def raise_for_status(self):pass
        class S:
            def post(_,url,json,timeout):
                self.assertEqual([x["range"] for x in json["data"]],["'01_SAN_XUAT'!C5","'01_SAN_XUAT'!D5"])
                return R()
        sh=object.__new__(runner.Sheets)
        sh.config=self.config;sh.url="https://unused";sh.session=S()
        sh.write(5,self.snapshot["headers"],{"idea_gpt":"GPT","idea_gemini":"Gemini"})

if __name__=="__main__":unittest.main()
