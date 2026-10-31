"""Read-only GitHub deployment approval provenance verifier.

The GitHub API response is untrusted until fetched via authenticated HTTPS
from api.github.com. Never treat this check alone as render authorization.
"""
from production_guard import GuardError

def verify_github_review(run, approvals, *, expected_commit, expected_environment="human-approval"):
    if not isinstance(run, dict) or not isinstance(approvals, list):
        raise GuardError("Missing GitHub approval evidence")
    if run.get("head_sha") != expected_commit or run.get("status") != "completed" or run.get("conclusion") != "success":
        raise GuardError("GitHub run not completed at expected commit")
    actor = run.get("actor") or {}
    initiator = actor.get("login", "")
    if not initiator:
        raise GuardError("Missing triggering actor")
    eligible = []
    for entry in approvals:
        user = (entry.get("user") or {}).get("login", "")
        environments = entry.get("environments") or []
        names = {e.get("name") for e in environments if isinstance(e, dict)}
        if entry.get("state") == "approved" and expected_environment in names and user and user.casefold() != initiator.casefold():
            eligible.append(user)
    if not eligible:
        raise GuardError("Independent GitHub reviewer approval not found")
    return {"source_commit": expected_commit, "initiator": initiator,
            "reviewer": eligible[-1], "run_id": str(run.get("id"))}
