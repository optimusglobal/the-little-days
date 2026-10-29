# V2.1 deployment checkpoint — 2026-10-29

- Architecture and implementation are staged in PR #2; main and PR #1/P0 remain unchanged.
- Code.js from commit f898c2f48b4fd9cce08ad05b836b9b75db572be8 has been copied into a newly created standalone Apps Script project. Clipboard readback matched source exactly. Manifest saved with explicit Sheets, Drive and external-request scopes; timezone Asia/Bangkok, V8.
- A separate native Google Sheet with PILOT!A1:G2 has been created and read back; IDEA_TEST is reserved in A2, B/C empty pending actual source analysis and GPT drafting. No fabricated source observations. Production Sheet untouched.
- A new private evidence folder has been created; permissions readback showed owner only. Private Google resource IDs remain in Script Properties, not this public repository.
- Five non-secret properties configured: TLD_ENABLED=false, sheet/tab/folder IDs, and gemini-3-flash-preview as candidate model pending live verification. GEMINI_API_KEY is not configured in this new project. Existing Mia key was not read or transferred.
- 14 local Node tests PASS. GitHub Check runner and Google native pilot both passed on commit 99067d657bd678ee8093834d6765b5598c562896. These are fixture tests, not evidence of live Gemini/Google execution.
- Remaining: owner configures private key and grants required OAuth access; run preflight, populate a real authorized IDEA_TEST, then run one Gemini review and cache-reuse check; GPT comparison/selection persistence comes next. Do not enable recurring triggers before pilot acceptance.
- No model request, production migration, render, billing or public deployment was performed. IDEA_002 remains paused.
