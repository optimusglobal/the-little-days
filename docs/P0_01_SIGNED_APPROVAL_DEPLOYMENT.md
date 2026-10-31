# P0-01 — Signed Approval Security (2026-10-28)

## Implemented
- Approval receipts are **schema v2** and require Ed25519 signature verification over canonical fields `schema_version, decision, idea_id, timeline_sha256, approved_by, key_id`.
- `approval_guard.py` uses trusted **public** key located at `~/.the-little-days/approval-trust/<key_id>.pem`; fails closed on unsigned, missing, modified, rejected or untrusted receipts.
- `approval_workflow.py` on Mia supports **review** and **verify** only. It cannot create an approval.
- `tools/approver_sign_offline.py` is an **offline-only utility**, which requires an externally provisioned Ed25519 private key, a human-confirmed exact timeline digest, and a reviewer identity.
- Test fixtures create **ephemeral** Ed25519 keys under temporary directories. No production private key was generated or deployed on Mia.
- Old schema v1 receipts are intentionally rejected.

## Mandatory deployment controls (NOT YET PERFORMED)
1. Provision a signing key on a **separately authorized approver device/account**, ideally backed by hardware keystore; private key MUST NOT be accessible to Mia, the render service, GitHub, or automation.
2. Provision the corresponding trusted public key into the machine's trust store using an admin-controlled mechanism; the renderer must **not be able to overwrite** the trusted public key or change its trust root.
3. Use OS ACLs so the render process can read receipts and trusted keys but **cannot alter the trust store or independently install other trusted keys**. Receipt signatures prevent undetected modifications when trust store is protected.
4. Bind `key_id` to a **verified approver identity and an explicit allowlist**; the unverified `approved_by` text alone is not identity proof.
5. Design documented key rotation, revocation, expiry, emergency denial and audit logging before production.
6. Re-run real dry run with a human-approved *non-held* test idea and verified trust-key provisioning.

## Residual risk
- **NO-GO**: Public key trust store is currently a local path; if the renderer can modify it, it can replace trusted keys and mint a matching receipt. Cryptographic verification does **not** enforce OS separation.
- `--reviewer` in offline signer is a self-declared label, not standalone identity authentication. The actual reviewer identity depends on independent key custody.
- No live approval receipt, signing key or elevated privileges were created.
