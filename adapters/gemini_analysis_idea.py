"""Gemini analysis/idea bridge for runner argv contract.

Only a real, locally provisioned MP4 is accepted. Gemini is called ONCE in
analysis using existing gemini_idea_review.py. Idea reuses its reviewed output.
No browser, render, Sheet writes, or fabricated provider evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gemini_idea_review import validate as validate_review

def write(path, value):
    path = Path(path)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def source_file(packet):
    source = str(packet["input"]["source"])
    # No arbitrary network downloads, and never interpret sheet URL as a command.
    if source.startswith(("https://example.invalid", "http://example.invalid")):
        raise ValueError("Demo source is not a real MP4")
    base = os.environ.get("WL_LOCAL_SOURCE_DIR")
    if not base:
        raise ValueError("WL_LOCAL_SOURCE_DIR is not configured")
    idea = packet["input"]["idea_id"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", idea):
        raise ValueError("Unsafe idea identifier")
    path = (Path(base).resolve() / (idea + ".mp4")).resolve()
    if path.parent != Path(base).resolve() or not path.is_file():
        raise ValueError("Trusted local MP4 missing")
    if path.stat().st_size > 15_000_000 or path.stat().st_size < 100:
        raise ValueError("Unsupported source size; use validated Files API for >15MB")
    return path

def execute(request, output):
    packet = json.loads(Path(request).read_text(encoding="utf-8"))
    stage = packet["stage"]
    result = Path(output)
    if stage == "analysis":
        path = source_file(packet)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        model = os.environ.get("WL_GEMINI_ANALYSIS_MODEL")
        if not model or not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise ValueError("Explicit supported Gemini model required")
        provider_output = result.with_name("gemini_source_review.json")
        # Existing Gemini implementation tracks pending responses; never retry
        # an uncertain request automatically.
        subprocess.run([sys.executable, str(ROOT / "gemini_idea_review.py"),
                        "--model", model, "--packet", str(Path(request).resolve()),
                        "--video", str(path), "--output", str(provider_output)],
                       check=True, timeout=900)
        evidence = json.loads(provider_output.read_text(encoding="utf-8"))
        review = evidence["review"]
        if not validate_review(review) or not evidence.get("approved"):
            raise ValueError("Gemini review did not approve source adaptation")
        if not review.get("source_transcript") or review.get("source_duration_seconds") is None:
            raise ValueError("Source dialogue/duration evidence insufficient")
        write(result, {
            "observations": {"source_transcript": review["source_transcript"],
                             "source_duration_seconds": review["source_duration_seconds"],
                             "review_verdict": review["verdict"]},
            "source_evidence": {"sha256": digest, "model": model,
                                "response_id": evidence.get("response_id"),
                                "transport": "Gemini API", "local_source": str(path)},
            "limitations": review.get("audio_limitations") or "None reported",
            "approved_content": review["final_content"],
            "review_record": evidence
        })
    elif stage == "idea":
        prior = packet.get("previous", {}).get("analysis", {})
        if prior.get("status") != "done":
            raise ValueError("Analysis must complete first")
        a = prior["result"]
        evidence = a.get("review_record", {})
        if not evidence.get("approved") or not validate_review(evidence.get("review", {})):
            raise ValueError("Missing real approved Gemini review")
        final = evidence["review"]["final_content"]
        if not all(isinstance(final.get(k), str) and final[k].strip()
                   for k in ("idea", "hook", "insight", "angle")):
            raise ValueError("Incomplete Gemini idea")
        write(result, {k: final[k] for k in ("idea", "hook", "insight", "angle")})
    else:
        raise ValueError("Only analysis and idea are supported")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Expected request and output paths")
    try:
        execute(sys.argv[1], sys.argv[2])
    except Exception as exc:
        print("Gemini adapter blocked: " + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2)
