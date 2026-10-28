# STEP 4.15.2C.3 — Automation Permission Isolation

Status: **PARTIAL / PRODUCTION NO-GO**. Tested on the feature branch only.

## Implemented and tested
- `tools/audit_approval_isolation.py` scans three approval test workflows for prohibited secret references, write permissions, unsafe triggers, missing `human-approval`, and persisted checkout credentials.
- `tests/test_approval_isolation.py` covers those fail-closed conditions.
- Mia local verification: **111/111 tests PASS**, static audit PASS.
- No private production key, signed production receipt, Mia render, Sheet update, or PR merge.

## Security boundaries
1. **GitHub test workflows:** non-privileged, read-only jobs; test signing uses a new disposable Ed25519 key, never trusted by Mia.
2. **Human reviewer:** GitHub environment approval is a workflow gate, *not* an independent cryptographic signing identity. The current account can self-review; do not treat this as a two-person control.
3. **Production signer:** must be isolated from GitHub workflow-editors and Mia. Its private key must not be committed, stored in runner secrets, copied to Mia, or available to autonomous jobs.
4. **Mia runner:** verification only using a pinned trusted Ed25519 public key; deny missing/changed receipts, historical locks, blocked status, and unapproved render requests.
5. **No implicit authority:** a successful GitHub job, ephemeral test signature, comment, commit, or workflow log cannot authorize production rendering.

## REQUIRED repository-owner controls (not verified or changed)
- Protect `main` and the future trusted workflow path with appropriate rulesets: required reviews, checks, restrictions on bypass and modification of workflow files. For a public repo, protect against untrusted contributors modifying code that can access any privileged environment.
- Restrict GitHub Actions permissions to read-only by default. Disable/limit unnecessary third-party actions; pin external actions to immutable SHAs for trusted production paths.
- Use **independent human identity** for production review and enforce **Prevent self-review**; current one-account configuration remains only a smoke-test setup.
- Before any production signing architecture is approved, choose isolated key storage and independent signer access; do not add `APPROVAL_SIGNING_KEY` to GitHub.
- Independently test that Mia fails closed on rejected, tampered, missing, and stale receipts as part of the final integration.

## Limitations
This static scanner is defense-in-depth, not a comprehensive YAML parser or GitHub repository permission auditor. Passing tests does **not** verify repository rulesets, environment reviewer identity, secret scope, branch protections, or filesystem ACLs. GitHub administration API returned access-denied during configuration inspection; no administrator settings were changed.

## Next decision
Owner to configure/confirm independent reviewer and GitHub protection rules. Keep IDEA_002 On-Hold; PR #1 unmerged; Production NO-GO.
