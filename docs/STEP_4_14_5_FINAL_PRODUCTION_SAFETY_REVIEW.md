# STEP 4.14.5 — Final Production Safety Review
Date: 2026-10-28
Branch: `feature/p0-render-safety-prompt-integrity`
Decision: **PRODUCTION NO-GO**; **SUPERVISED LIVE PILOT CONDITIONAL NO-GO** (requirements below).

## Evidence reviewed
- Offline suite: 102/102 tests PASS at STEP 4.14.4 on Mia; latest commit `4a72158b` GitHub Actions two runs PASS.
- Real read-only Sheet/Drive dry run: IDEA_002 sheet PASS, L5 PASS, Frame PASS, historical_lock BLOCK, status `Bị chặn`, decision NO_GO, render NEVER_SUBMITTED.
- Offline mock E2E covers signed receipt, live packet comparisons, character/dialogue/source contracts, synthetic multi-segment exporter, no actual browser calls.

## Mandatory blockers for unattended production
1. **APPROVAL TRUST — NOT DEPLOYED:** Ed25519 verification exists; no protected trust root or separate key custody / OS ACL / signer authorization established on Mia. Current approval trust path is writable by its owning user unless OS permissions are configured. Signature alone is not separation of duties.
2. **RECOVERY EXCEPTION — AUDIT NEEDED:** `run_browser.py` bypasses normal live packet/status/approval preflight when `--conversation` is used. Intended for recovery without resubmission, but adoption/download actions must be separately authorized; enforce no new submit and verify immutable job binding.
3. **PROVENANCE & MANIFEST — PARTIAL:** Source dialogue scanner recognizes `Speaker: "..." ` structured lines only. It cannot prove complete fidelity for unstructured storyboards or infer whether image L5 depicts the required character; runtime guard validates asset hashes but not visual/voice semantics.
4. **L5 IMAGE CONTENT — PARTIAL:** Real read-only dry run checks Drive metadata; offline exporter checks downloaded hashes. No end-to-end real Drive byte-level validation against an independently pinned reference hash for current L5.
5. **PROVIDER/RECOVERY — UNVERIFIED:** Gemini UI, model selection, first real provider submission, job resume after network interruption and no-duplicate behavior have not been tested in a controlled live pilot.
6. **VIDEO QC — UNVERIFIED:** Speech timing, exact dialogue delivery, expression, character consistency, and transitions cannot be proven by static prompt validators.

## Required conditions before ONE supervised pilot (not IDEA_002)
- Select a new, explicitly approved, non-held test idea. Preserve IDEA_002 historical lock and `Bị chặn`.
- Configure a protected approver trust key and human approval receipt; never use ephemeral test signing keys.
- Close `--conversation` recovery guard issue and rehearse failure/recovery offline.
- Verify exact source dialogue transcript, timeline, identity source L5, per-segment prompt, planned provider/model/quota; record user confirmation for any charge-bearing render.
- Run read-only Sheet/Drive checks immediately before submission; allow only one controlled render attempt, no automatic retries.
- Perform human review of delivered video before any repeat/render expansion.

## Criteria for production GO
All above plus protected signer identity and key rotation/revocation, end-to-end integration of real data & assets, acceptance thresholds for QC, documented operations and incident response, reproducible CI on release commit, and explicit owner approval. Keep PR #1 draft and unmerged until gates close.

## Explicitly not performed
No live video generated, no Sheet/checkbox changes, no human approval receipt created for IDEA_002, no merge, no production ledger mutation.
