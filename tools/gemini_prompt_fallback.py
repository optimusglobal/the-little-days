"""Fail-closed Gemini model fallback for prompt authoring.

Each model has its own durable response and pending record. Only explicit HTTP
404 or 503 with a persisted provider error permits a different model.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

def run_fallback(brief, output_dir, models, worker=None):
    root=Path(output_dir);root.mkdir(parents=True,exist_ok=True)
    if not models or len(models)>3 or len(set(models))!=len(models):
        raise ValueError("Provide 1-3 unique fallback models")
    if any(not re.fullmatch(r"[A-Za-z0-9._-]+",model) for model in models):
        raise ValueError("Invalid model identifier")
    worker=Path(worker) if worker else Path(__file__).resolve().parents[1]/"gemini_flow_prompt_revision.py"
    results=[]
    for index,model in enumerate(models):
        target=root/("prompt_%02d.json"%index)
        if target.exists():
            data=json.loads(target.read_text(encoding="utf-8"))
            if data.get("model")!=model:raise ValueError("Model mismatch in existing result")
            return {"status":"ready","model":model,"output":str(target),"reused":True}
        response=target.with_suffix(".response.json")
        pending=target.with_suffix(".pending.json")
        errors=target.with_suffix(".errors.json")
        if response.exists():
            return {"status":"blocked_reconcile_response","model":model}
        if pending.exists():
            if not errors.exists():return {"status":"blocked_pending","model":model}
            report=json.loads(errors.read_text(encoding="utf-8")).get("errors",[])
            if not report or report[-1].get("http_status") not in (404,503):
                return {"status":"blocked_pending","model":model}
            # HTTP 503 may mean the server processed the request; no automatic
            # duplicate within this model. A different model is allowed only
            # after the explicit terminal error and no saved response.
            if report[-1].get("retry_delay_seconds") is not None:
                return {"status":"blocked_retry_not_terminal","model":model}
            results.append({"model":model,"http_status":report[-1]["http_status"]})
            continue
        proc=subprocess.run([sys.executable,str(worker),"--brief",str(brief),
                             "--output",str(target),"--model",model],
                            capture_output=True,text=True,timeout=900)
        if proc.returncode==0 and target.exists():
            return {"status":"ready","model":model,"output":str(target),"reused":False}
        if response.exists():return {"status":"blocked_reconcile_response","model":model}
        if errors.exists():
            report=json.loads(errors.read_text(encoding="utf-8")).get("errors",[])
            if report and report[-1].get("http_status") in (404,503) and report[-1].get("retry_delay_seconds") is None:
                results.append({"model":model,"http_status":report[-1]["http_status"]})
                continue
        return {"status":"blocked_unclassified","model":model}
    return {"status":"blocked_all_models","attempts":results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--brief",required=True);p.add_argument("--output-dir",required=True)
    p.add_argument("--models",nargs="+",required=True)
    a=p.parse_args()
    result=run_fallback(a.brief,a.output_dir,a.models)
    print(json.dumps(result))
    if result["status"]!="ready":sys.exit(2)
