"""Read-only MVP readiness probe: never submits AI requests, writes Sheets, or renders."""
import argparse
import json
import shutil
from pathlib import Path
import runner

STAGES = ("analysis", "idea", "script", "frame", "prompt")

def report(config, snapshot):
    entries = runner.plan(snapshot, config)
    workers = config.get("workers") or {}
    stages = []
    dependency_blocked = False
    for stage in STAGES:
        command = workers.get(stage)
        configured = isinstance(command, list) and len(command) >= 2 and all(isinstance(x, str) and x for x in command)
        executable = bool(configured and (shutil.which(command[0]) or Path(command[0]).is_file()))
        script_exists = bool(configured and Path(command[1]).is_file())
        runnable = bool(configured and executable and script_exists)
        status = "configured_unverified" if runnable else "missing_adapter"
        stages.append({"stage": stage, "status": status, "command": command if configured else None})
        if not runnable: dependency_blocked = True
    return {"mode": "no_api_no_sheet_no_render", "eligible_rows": len(entries),
            "stages": stages, "ready_for_live_execution": False,
            "blocking_stage": next((s["stage"] for s in stages if s["status"] == "missing_adapter"), None),
            "note": "Runnable argv is not proof that real Gemini/video/image review succeeded."}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.example.json")
    ap.add_argument("--snapshot", default="examples/input.json")
    args = ap.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    print(json.dumps(report(config, snapshot), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
