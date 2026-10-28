import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from adapters.reviewed_frame import execute

class FrameHandoffTests(unittest.TestCase):
    def _make(self, directory):
        root=Path(directory)
        img=root/"frame.png";img.write_bytes(b"verified-image-content-for-test")
        entry={"idea_id":"DEMO","revision":"r1","reference":"L5-ref"}
        manifest={"idea_id":"DEMO","source_revision":"r1","image_file":"frame.png",
            "reference_evidence":{"cell":"L","identity_row":5,"input":"L5-ref",
                                  "sha256":hashlib.sha256(img.read_bytes()).hexdigest()},
            "qc":{"verdict":"ready","evidence":"reviewed image"}}
        (root/"DEMO.frame.json").write_text(json.dumps(manifest))
        req=root/"request.json"
        req.write_text(json.dumps({"stage":"frame","input":entry,
                      "previous":{"script":{"status":"done"}}}))
        return req, root/"result.json"
    def test_accepts_reviewed_image_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            req,out=self._make(d)
            with patch.dict(os.environ,{"WL_FRAME_HANDOFF_DIR":d}):
                execute(req,out)
            self.assertEqual(json.loads(out.read_text())["reference_evidence"]["identity_row"],5)
    def test_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            req,out=self._make(d)
            (Path(d)/"frame.png").write_bytes(b"tampered image contents")
            with patch.dict(os.environ,{"WL_FRAME_HANDOFF_DIR":d}):
                with self.assertRaises(ValueError):execute(req,out)
            self.assertFalse(out.exists())
    def test_rejects_other_identity_row(self):
        with tempfile.TemporaryDirectory() as d:
            req,out=self._make(d)
            file=Path(d)/"DEMO.frame.json";m=json.loads(file.read_text())
            m["reference_evidence"]["identity_row"]=6
            file.write_text(json.dumps(m))
            with patch.dict(os.environ,{"WL_FRAME_HANDOFF_DIR":d}):
                with self.assertRaises(ValueError):execute(req,out)
if __name__=="__main__":unittest.main()
