"""Fail-closed static isolation checks for GitHub approval smoke tests.

This guard intentionally does not grant approval or examine any production secret.
It detects changes that would turn test-only workflows into privileged render paths.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ".github/workflows/human-approval-test.yml",
    ".github/workflows/timeline-approval.yml",
    ".github/workflows/signed-receipt-ephemeral-test.yml",
)
BLOCKED = (
    r"\$\{\{\s*secrets\.",
    r"\b(?:APPROVAL_SIGNING_KEY|PRIVATE_KEY|DEPLOY_KEY|ACTIONS_ID_TOKEN_REQUEST_TOKEN)\b",
    r"\b(?:pull_request_target|workflow_run)\s*:",
    r"\b(?:contents|actions|deployments|id-token)\s*:\s*write\b",
    r"\b(?:render|submit|deploy)[-_ ]?(?:video|job|production)\b",
    r"\b(?:curl|wget)\b.*(?:https?://)",
)
def validate_workflow(path):
    s = Path(path).read_text(encoding="utf-8")
    problems = []
    if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", s):
        problems.append("requires explicit contents: read permissions")
    if re.search(r"(?m)^\s*environment:\s*human-approval\s*$", s) is None:
        problems.append("human-approval environment is missing")
    if not re.search(r"(?m)^\s*persist-credentials:\s*false\s*$", s) and "checkout@" in s:
        problems.append("checkout must disable persisted credentials")
    for pattern in BLOCKED:
        if re.search(pattern, s, re.IGNORECASE):
            problems.append("forbidden privileged token/pattern: " + pattern)
    return problems

def audit(root=ROOT):
    findings = {}
    for relative in WORKFLOWS:
        path = Path(root) / relative
        if not path.is_file():
            findings[relative] = ["required workflow absent"]
        else:
            issues = validate_workflow(path)
            if issues:
                findings[relative] = issues
    return findings

if __name__ == "__main__":
    results = audit()
    if results:
        for path, problems in results.items():
            for problem in problems:
                print("ISOLATION_FAIL", path, problem)
        raise SystemExit(2)
    print("ISOLATION_STATIC_CHECK_PASS: test workflows read-only, human-gated, no secrets/render")
