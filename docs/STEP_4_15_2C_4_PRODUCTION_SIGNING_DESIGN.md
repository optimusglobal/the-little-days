# STEP 4.15.2C.4 — Independent Human Approval and Production Signing Design

**Status: DESIGN + CONTRACT TESTS PASS; PRODUCTION NO-GO.**

## Trust boundaries

1. **GitHub:** stores reviewed source code, immutable timeline commit and hash. Its test-only `human-approval` environment currently permits self-review and does not attest to an independent human identity. A green Actions run is **not** a production receipt.
2. **Independent reviewer:** must use a different GitHub identity from the committer/initiator and review the exact timeline hash, source commit, and content. Configure `Prevent self-review` only when reviewer is available. Approval event review and actual source/digest binding must be verified in the eventual evidence integration.
3. **Offline signer:** has the Ed25519 private key, on a separate approved device **not Mia, GitHub Actions, a shared repo, or production secrets**. It should only sign after explicit authenticated review of digest and artifact, with audit evidence linking the reviewer to the source revision. Existing `tools/approver_sign_offline.py` supports the schema-v2 signed fields but does **not** itself verify a GitHub review event.
4. **Mia:** holds only a pinned public verification key, alongside guarded local approval records; calls `approval_guard.verify_approval` prior to any render. Missing, modified, untrusted, or mismatched receipts fail closed.
5. **Runtime:** checks on-hold state, historical locks, render budgets, script/prompt integrity and the signed approval separately; no isolated check substitutes for the others.

## Schema-v2 receipt — current compatibility

Signature covers `schema_version`, `decision`, `idea_id`, `timeline_sha256`, `approved_by`, and `key_id`. It does **not** cover a source commit, review event ID, expiry, environment, or individual render authorization. Therefore it must **not** be treated as a complete verifiable GitHub Human Approval-to-Mia production chain.

## Verified in the P0 branch

- `tests/test_production_signing_contract.py`: ephemeral key tests for valid signature, changed timeline, fake reviewer, missing/untrusted key, wrong digest, fake inline approval.
- Complete Mia suite: **119/119 passed**, approval workflow isolation static scan passed. No production key or real receipt.
- Main ruleset/settings reported applied and verified by user via ChatGPT Work; not independently administratively revalidated here.

## Production go-live blockers

1. Independent reviewer identity and `Prevent self-review` with evidence of reviewer/trigger actor separation.
2. Define and implement a **versioned schema-v3** receipt or separately authenticated attestation that binds source commit, timeline SHA-256, GitHub review event identity, and intended production action. Add replay/expiry/revocation policy and tests without weakening v2 compatibility.
3. Provision independent signing device, offline private key, strict public-key trust store and rotation policy; no private key on Mia/GitHub.
4. Confirm trusted release/runner code is protected against changes and bypass; complete adversarial tests with revoked/stale/forged evidence.
5. Obtain explicit owner go-live authorization after independent security review; IDEA_002 remains On-Hold.

**Do not:** merge PR #1, render, change Google Sheet admin cells, store production signing secrets, or create real approved receipts during this work.
