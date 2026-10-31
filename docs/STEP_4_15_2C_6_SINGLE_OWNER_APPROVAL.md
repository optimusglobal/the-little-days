# STEP 4.15.2C.6 — Single-Owner Offline Approval (P0 Design)

**Status: verifier and unit tests completed; production authorization remains NO-GO.**

## Security model
- One human owner may submit code and approve a specific timeline, but the approval must use an independent, owner-held cryptographic authenticator rather than merely GitHub's self-review.
- GitHub deployment approval is a workflow gate and audit signal, **not** the security boundary for a single-owner configuration.
- Separate private signing key must reside outside GitHub, Mia, and all autonomous runtime environments. The public verification key must be pinned and managed as trusted configuration, not supplied by an untrusted receipt.
- `owner_approval.verify_owner_proof` checks an Ed25519 signature over exact idea, timeline SHA-256, source commit, owner identity, key ID, and a challenge. It does not generate keys or receipts and **does not authorize render**.
- Legacy two-person `approval_v3.py` and `github_review_evidence.py` remain unmodified; no unsafe self-review override has been added.

## Verified
- Synthetic valid owner proof accepted.
- Missing proof, fake inline approval, GitHub self-review-only proof, changed timeline/commit, altered signature, untrusted key, incorrect challenge and caller-provided replay set are rejected.
- **152/152 tests PASS on Mia**, plus workflow isolation static audit PASS.

## Outstanding critical controls (do not bypass)
1. **Challenge lifecycle:** generate random challenges in a trusted location, record single-use redemption in an atomic durable ledger, enforce expiration, and ensure a race cannot redeem the same proof twice. Current `used_challenges` argument alone is NOT a durable replay defense.
2. **Trusted source:** bind the exact reviewed commit and artifact to an authenticated source; do not accept arbitrary claimed commits.
3. **Owner key enrollment:** securely provision and pin a public key; private key must be on an independently controlled signing device. No production keys created.
4. **Render integration:** wire the verifier into the admission path with blocked status, historical locks, render budget, and explicit owner confirmation. Existing check does NOT authorize execution.
5. **Review and go-live:** owner explicitly approves a complete security plan and human owner action. Do not treat these isolated unit tests as a production safety guarantee.

No PR merge, IDEA_002 render, Google Sheet writes, production secrets, or real receipt creation permitted in this stage.
