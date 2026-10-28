"""Frame 0 admission adapter. Verifies actual local image bytes and L5 provenance.

This is an evidence-based handoff, NOT an image generation tool.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

def execute(request_path, output_path):
    packet=json.loads(Path(request_path).read_text(encoding="utf-8"))
    if packet.get("stage")!="frame": raise ValueError("Expected frame stage")
    entry=packet.get("input",{})
    idea=entry.get("idea_id","")
    if not isinstance(idea,str) or not idea or not all(c.isalnum() or c in "_-" for c in idea):
        raise ValueError("Invalid idea ID")
    if not entry.get("reference"): raise ValueError("Missing canonical L reference")
    prior=packet.get("previous",{})
    if prior.get("script",{}).get("status")!="done":
        raise ValueError("Approved script required")
    root=Path(os.environ.get("WL_FRAME_HANDOFF_DIR","")).resolve() if os.environ.get("WL_FRAME_HANDOFF_DIR") else None
    if not root or not root.is_dir(): raise ValueError("WL_FRAME_HANDOFF_DIR unavailable")
    manifest=root/(idea+".frame.json")
    if manifest.is_symlink() or not manifest.is_file(): raise ValueError("Frame evidence missing")
    record=json.loads(manifest.read_text(encoding="utf-8"))
    if record.get("idea_id")!=idea or record.get("source_revision")!=entry.get("revision"):
        raise ValueError("Frame handoff revision mismatch")
    reference=record.get("reference_evidence",{})
    if not isinstance(reference,dict) or reference.get("cell")!="L" or reference.get("input")!=entry["reference"] or reference.get("identity_row")!=5:
        raise ValueError("All character identities must be anchored to L5")
    image_name=record.get("image_file","")
    if not isinstance(image_name,str) or Path(image_name).name!=image_name or not image_name.lower().endswith((".png",".jpg",".jpeg")):
        raise ValueError("Image file must be a safe local basename")
    image=root/image_name
    if image.is_symlink() or not image.is_file() or image.stat().st_size<16:
        raise ValueError("Frame 0 image bytes unavailable")
    image_hash=hashlib.sha256(image.read_bytes()).hexdigest()
    if reference.get("sha256")!=image_hash:
        raise ValueError("Frame hash mismatch")
    qc=record.get("qc",{})
    if not isinstance(qc,dict) or qc.get("verdict")!="ready" or not qc.get("evidence"):
        raise ValueError("Independent frame QC evidence missing")
    result={"frame":str(image),"reference_evidence":reference,"qc":qc}
    target=Path(output_path); temp=target.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    os.replace(temp,target)
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit(2)
    try: execute(sys.argv[1],sys.argv[2])
    except Exception as exc:
        print("Frame handoff blocked: "+type(exc).__name__,file=sys.stderr)
        raise SystemExit(2)
