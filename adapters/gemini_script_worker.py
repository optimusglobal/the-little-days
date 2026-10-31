"""Gemini-backed script worker for runner; preserves raw response and blocks replay."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gemini_idea_review import api,write

EXPECTED=[("Daughter","Mama, no."),("Mother","No?"),("Daughter","Dad do."),("Father","Me?"),("Daughter","Yes."),("Daughter","Mama!"),("Father","Yes, boss.")]
RULES="""Write and critically review an original US-English 3D family comedy storyboard based on the input source transcription and approved idea. Character identity MUST come from canonical L5: Mother left in terracotta and cream, Father right in sage and jeans, Daughter center in peach dress and two pigtails. Video source clothing is NOT the character identity. Daughter kisses/hugs MOTHER. One pair of shoes only. Preserve every approved line, exact speaker and order. Provide enough time for natural acting; split into two clips if needed, never omit or shorten lines. Return JSON OBJECT with fields: verdict (ready or revise or insufficient_evidence), reason, script (complete formatted storyboard with attributed spoken lines), dialogue_manifest (list of {speaker,text}), segments (array of {duration_seconds,lines}), total_duration_seconds, review_evidence (concrete reasoning that dialogue, timing, identity, staging were checked). Do not say ready without careful review. Summaries Vietnamese, dialogue US English."""
def execute(request,output):
    pkt=json.loads(Path(request).read_text(encoding="utf-8"))
    if pkt.get("stage")!="script":raise ValueError("Wrong stage")
    previous=pkt.get("previous",{})
    for stage in ("analysis","idea"):
        if previous.get(stage,{}).get("status")!="done":raise ValueError("Missing "+stage)
    idea=pkt.get("input",{}).get("idea_id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",idea):raise ValueError("Unsafe idea ID")
    analysis=previous["analysis"]["result"]
    transcript=analysis.get("observations",{}).get("source_transcript")
    if not isinstance(transcript,list) or not transcript:raise ValueError("Missing source transcript")
    source=[(x.get("speaker"),x.get("text")) for x in transcript]
    if source!=EXPECTED:raise ValueError("Source dialogue not verified against approved turns")
    idea_result=previous["idea"]["result"]
    if any(not idea_result.get(k) for k in ("idea","hook","insight","angle")):
        raise ValueError("Missing approved idea")
    model=os.environ.get("WL_GEMINI_SCRIPT_MODEL","")
    if not re.fullmatch(r"[A-Za-z0-9._-]+",model):raise ValueError("Configure WL_GEMINI_SCRIPT_MODEL")
    target=Path(output)
    record=target.with_name("gemini_script_review.json")
    brief={"idea_id":idea,"revision":pkt["input"]["revision"],"source_transcript":transcript,
           "idea":idea_result,"reference":"L5 only","required_dialogue":EXPECTED}
    digest=hashlib.sha256(json.dumps({"brief":brief,"model":model},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if target.exists():return
    if record.exists():
        saved=json.loads(record.read_text(encoding="utf-8"))
        if saved.get("input_sha256")!=digest:raise ValueError("Prior review input mismatch")
        raw=saved["provider_response"]
    else:
        pending=record.with_suffix(".pending.json")
        response=record.with_suffix(".response.json")
        if response.exists():
            raw=json.loads(response.read_text(encoding="utf-8"))
        else:
            if pending.exists():raise ValueError("Pending Gemini script request needs reconciliation")
            write(pending,{"input_sha256":digest,"model":model})
            raw=api("models/"+model+":generateContent",{
                "systemInstruction":{"parts":[{"text":RULES}]},
                "contents":[{"role":"user","parts":[{"text":json.dumps(brief,ensure_ascii=False)}]}],
                "generationConfig":{"responseMimeType":"application/json"}},
                error_log=record.with_suffix(".errors.json"))
            write(response,raw)
    candidate=raw.get("candidates",[{}])[0]
    if candidate.get("finishReason")!="STOP":raise ValueError("Incomplete provider response")
    content=json.loads("".join(x.get("text","") for x in candidate.get("content",{}).get("parts",[]) if not x.get("thought")))
    if isinstance(content,list) and len(content)==1 and isinstance(content[0],dict):content=content[0]
    if not isinstance(content,dict):raise ValueError("Expected Gemini JSON object")
    turns=content.get("dialogue_manifest",[])
    if not isinstance(turns,list) or [(x.get("speaker"),x.get("text")) for x in turns]!=EXPECTED:
        raise ValueError("Gemini changed or omitted dialogue")
    if content.get("verdict")!="ready" or not content.get("review_evidence"):
        raise ValueError("Gemini script review not ready")
    script=content.get("script")
    if not isinstance(script,str) or not script.strip():raise ValueError("Missing storyboard")
    segments=content.get("segments")
    if not isinstance(segments,list) or not segments:raise ValueError("Missing timeline")
    duration=content.get("total_duration_seconds")
    if type(duration) not in (int,float) or duration<10.5:
        raise ValueError("Insufficient timeline duration")
    write(record,{"input_sha256":digest,"model":model,"response_id":raw.get("responseId"),
                  "provider_response":raw,"review":content})
    write(target,{"script":script,"review":{"provider":"Gemini","verdict":"ready",
                  "evidence":{"response_id":raw.get("responseId"),"model":model,
                              "dialogue_manifest":turns,"segments":segments,
                              "duration_seconds":duration,"review":content["review_evidence"]}}})
    record.with_suffix(".pending.json").unlink(missing_ok=True)
if __name__=="__main__":
    try:
        if len(sys.argv)!=3:raise ValueError("Expected request result paths")
        execute(sys.argv[1],sys.argv[2])
    except Exception as e:
        print("Gemini script worker BLOCKED: "+type(e).__name__+" "+str(e),file=sys.stderr)
        sys.exit(2)
