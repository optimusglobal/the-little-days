"""Conservative Script/Prompt workers; only trusted reviewed handoff artifacts.

No invented Gemini review, no image fabrication, no render. These workers
consume externally produced, evidence-bearing results and fail closed if absent.
"""
import json
import sys
from pathlib import Path

def execute(request_path, output_path):
    packet=json.loads(Path(request_path).read_text(encoding="utf-8"))
    stage=packet.get("stage")
    if stage not in ("script","prompt"):
        raise ValueError("Only script and prompt handoff supported")
    input_data=packet.get("input",{})
    idea=input_data.get("idea_id")
    if not isinstance(idea,str) or not idea or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in idea):
        raise ValueError("Invalid idea ID")
    root=Path(__file__).resolve().parents[1]
    approved=root/".runtime"/"reviewed_handoffs"/(idea+"."+stage+".json")
    if not approved.is_file():
        raise ValueError("Missing reviewed handoff: no AI output may be invented")
    evidence=json.loads(approved.read_text(encoding="utf-8"))
    if evidence.get("idea_id")!=idea or evidence.get("source_revision")!=input_data.get("revision"):
        raise ValueError("Handoff revision mismatch")
    if stage=="script":
        if (not isinstance(evidence.get("script"),str) or not evidence["script"].strip()
                or not isinstance(evidence.get("review"),dict)
                or evidence["review"].get("provider")!="Gemini"
                or evidence["review"].get("verdict")!="ready"
                or not evidence["review"].get("evidence")):
            raise ValueError("Real Gemini script review required")
        result={"script":evidence["script"],"review":evidence["review"]}
    else:
        prior=packet.get("previous",{})
        if prior.get("frame",{}).get("status")!="done":
            raise ValueError("Reviewed Frame 0 evidence required first")
        if prior.get("script",{}).get("status")!="done":
            raise ValueError("Reviewed script required first")
        if not isinstance(evidence.get("prompt"),str) or not evidence["prompt"].strip():
            raise ValueError("Reviewed US English prompt missing")
        if evidence.get("review",{}).get("provider")!="Gemini" or evidence["review"].get("verdict")!="ready":
            raise ValueError("Actual Gemini prompt review required")
        result={"prompt":evidence["prompt"]}
    out=Path(output_path)
    temp=out.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(out)
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: worker request.json result.json")
    try: execute(sys.argv[1],sys.argv[2])
    except Exception as exc:
        print("Reviewed handoff blocked: "+type(exc).__name__,file=sys.stderr)
        raise SystemExit(2)
