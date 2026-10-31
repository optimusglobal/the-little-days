# P0 Production Safety Audit — 2026-10-28

**Decision: NO-GO.** This is a code review + offline integration report, not a live video certification.

## Evidence
- Offline E2E: real timeline validator, independent receipt verifier, live-packet comparison logic (mocked Sheet), production status, historical lock and ledger admission, with fake Job/MCP in a temporary directory.
- Positive path: one **mock** submission allowed after matching receipt and explicit send flag.
- Negative paths: missing approval receipt, modified approved timeline, blocked live row, absent send confirmation => zero mock submissions.
- No Gemini/Flow calls, no live Sheet mutation, no production ledger writes.

## Open blockers
1. **HIGH — Approval authority is not authenticated.** `approval_workflow.py approve` accepts self-declared `--reviewer` and SHA copied from review. A process with write access to the approvals directory can mint a receipt. A cryptographic signer or separately authorized approval identity and restrictive ACL are required for adversarial resistance.
2. **HIGH — Preparation side effects before live authorization.** `run_browser.py` creates Job/MCP and can call `job.prepare()` before `verify_packet_live()` and `verify_approval()`, which currently run immediately before `job.submit()`. No render is sent without checks in the normal CLI path, but blocked rows can still trigger browser interactions/file uploads. Move read-only eligibility checks ahead of browser preparation; preserve explicit recovery flow.
3. **HIGH — Real multi-segment export not E2E verified.** Current E2E test uses a prepared packet with mocked Sheet and Job. Separate test needed for exporter and Drive image bytes, including L5 SHA256, segment isolation and race/staleness.
4. **MEDIUM — Approval receipts do not carry expiration/revocation policy.** Existing receipts are non-overwritable by default, but lifecycle for revoked approval and explicit re-approval has not been built.
5. **MEDIUM — Non-submit paths/recovery are not live audited.** Adoption/download of existing videos should be explicitly distinguished from permission to initiate rendering.
6. **MEDIUM — Real Gemini model selection, UI flow, video semantic QC and duration/voice correctness remain unverified.** Passing offline tests does not certify video fidelity.

## Required release gate
- CI green on current commit, deterministic E2E green, authenticated approval model, pre-prepare fail-closed guard, exporter/Drive integration coverage, failure/recovery drills, and first human-approved limited live pilot.
- Keep IDEA_002 on hold; do not create approval receipt for it.
- Keep PR #1 unmerged until gates close.
