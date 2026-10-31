"""Runner prompt worker using durable Gemini model fallback.

Requires completed script and Frame 0 with QC. No render or Sheet writes.
"""
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.gemini_prompt_fallback import run_fallback

EXPECTED=[("Daughter","Mama, no."),("Mother","No?"),("Daughter","Dad do."),
          ("Father","Me?"),("Daughter","Yes."),("Daughter","Mama!"),("Father","Yes, boss.")]

def execute(request_path,output_path):
    packet=json.loads(Path(request_path).read_text(encoding="utf-8"))
    if packet.get("stage")!="prompt":raise ValueError("Not prompt stage")
    prev=packet.get("previous",{})
    for name in ("analysis","idea","script","frame"):
        if prev.get(name,{}).get("status")!="done":raise ValueError("Missing completed "+name)
    entry=packet["input"]
    idea=entry.get("idea_id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",idea):raise ValueError("Unsafe idea ID")
    frame=prev["frame"]["result"]
    if frame.get("reference_evidence",{}).get("identity_row")!=5:
        raise ValueError("L5 identity evidence required")
    if frame.get("qc",{}).get("verdict")!="ready":raise ValueError("Frame QC required")
    source_review=prev["analysis"]["result"]
    if not source_review.get("source_evidence",{}).get("sha256"):
        raise ValueError("Source media hash required")
    models=[x.strip() for x in os.environ.get("WL_GEMINI_PROMPT_MODELS","").split(",") if x.strip()]
    if not models:raise ValueError("Configure WL_GEMINI_PROMPT_MODELS explicitly")
    target=Path(output_path)
    folder=target.parent/"gemini_prompt_fallback"
    folder.mkdir(parents=True,exist_ok=True)
    brief_path=folder/"brief.json"
    brief={"idea_id":idea,"revision":entry["revision"],
           "canonical_identity":"L5 only; mother LEFT terracotta/cream, father RIGHT sage/jeans, daughter CENTER peach dress",
           "source_transcript":source_review["observations"]["source_transcript"],
           "script":prev["script"]["result"]["script"],
           "frame_path":frame["frame"],
           "frame_reference_evidence":frame["reference_evidence"],
           "owner_rules":"Exact seven approved turns and speakers, natural US dialogue; no missing lines, no extra shoes, child hugs mother; split if needed."}
    desired=json.dumps(brief,ensure_ascii=False,sort_keys=True)
    if brief_path.exists() and brief_path.read_text(encoding="utf-8")!=desired:
        raise ValueError("Brief changed in existing revision; manually reconcile")
    if not brief_path.exists():brief_path.write_text(desired,encoding="utf-8")
    result=run_fallback(brief_path,folder,models)
    if result["status"]!="ready":raise ValueError("Gemini fallback: "+result["status"])
    record=json.loads(Path(result["output"]).read_text(encoding="utf-8"))
    payload=record.get("result",{})
    if payload.get("approved") is not True or payload.get("verdict")!="ready":
        raise ValueError("Gemini did not approve prompt")
    turns=payload.get("part1_lines",[])+payload.get("part2_lines",[])
    if [(x.get("speaker"),x.get("text")) for x in turns]!=EXPECTED:
        raise ValueError("Dialogue coverage mismatch")
    if not all(isinstance(payload.get(x),str) and payload[x].strip() for x in ("master_prompt","part1_prompt","part2_prompt")):
        raise ValueError("Missing prompt content")
    target.write_text(json.dumps({"prompt":json.dumps({"master":payload["master_prompt"],
               "part1":payload["part1_prompt"],"part2":payload["part2_prompt"]},ensure_ascii=False),
               "review":{"provider":"Gemini","verdict":"ready","response_id":record.get("response_id"),"model":record["model"]}},
               ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":
    try:
        if len(sys.argv)!=3:raise ValueError("Expected request and output")
        execute(sys.argv[1],sys.argv[2])
    except Exception as exc:
        print("Prompt worker BLOCKED: "+type(exc).__name__+" "+str(exc),file=sys.stderr)
        sys.exit(2)
