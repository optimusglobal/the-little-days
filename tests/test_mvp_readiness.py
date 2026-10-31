import json
import unittest
from pathlib import Path
from tools.mvp_readiness import report

class MVPReadinessTests(unittest.TestCase):
    def test_unconfigured_workers_report_all_gaps_without_side_effects(self):
        cfg=json.loads(Path("config.example.json").read_text(encoding="utf-8"))
        snap=json.loads(Path("examples/input.json").read_text(encoding="utf-8"))
        result=report(cfg,snap)
        self.assertEqual(result["eligible_rows"],1)
        self.assertEqual(result["blocking_stage"],"analysis")
        self.assertEqual([s["stage"] for s in result["stages"]],["analysis","idea","script","frame","prompt"])
        self.assertTrue(all(s["status"]=="missing_adapter" for s in result["stages"]))
        self.assertFalse(result["ready_for_live_execution"])
    def test_missing_worker_file_rejected(self):
        cfg=json.loads(Path("config.example.json").read_text(encoding="utf-8"))
        snap=json.loads(Path("examples/input.json").read_text(encoding="utf-8"))
        cfg["workers"]={"analysis":["python","adapters/not_implemented.py"]}
        self.assertEqual(report(cfg,snap)["stages"][0]["status"],"missing_adapter")

if __name__=="__main__":unittest.main()
