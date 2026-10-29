# Google-native pilot deployment

Source: Code.js + appsscript.json, version 2.1.0. Code.js is uploaded as Code.gs in Apps Script V8. Keep the source identical to a known GitHub commit. Do not enable a public web app.

1. Create a standalone Apps Script project under the intended Google account.
2. Copy the reviewed Code.js into Code.gs. Enable manifest visibility in project settings and copy appsscript.json. Apps Script requests Sheets, Drive, external-request scopes; these OAuth scopes are broad even though code limits access to configured IDs. Obtain account-owner consent before granting them. Do not claim folder-only OAuth access.
3. Create a separate pilot Sheet/tab with row1 exactly: idea_id, source_analysis, idea_gpt, idea_gemini, review_link, state, input_hash. Row2 idea_id must be IDEA_TEST. Do not use the legacy production sheet.
4. Configure Script Properties: TLD_SHEET_ID, TLD_TAB, TLD_FOLDER_ID (private output folder), TLD_MODEL (verify an accessible Gemini model), TLD_ENABLED=false. Enter GEMINI_API_KEY yourself in Script Properties; never in code/chat. Properties are visible to project editors, so do not share edit access broadly. No new production key or billing is required automatically.
5. Run preflight after account-owner OAuth consent. It reads schema/folder/key presence, never calls AI. Missing config/key stops clearly.
6. Populate verified source_analysis and GPT idea; keep D/E/G empty. Set TLD_ENABLED=true for the single authorized pilot, then run runPilot. No trigger is installed. Retain output artifacts privately.
7. Inspect independent Gemini rewrite, critique/report and preserved GPT; run again to verify CACHE_HIT without another provider call. Set TLD_ENABLED=false afterwards.
8. On SUBMITTING/AMBIGUOUS/WAITING_* or INVALID_RESPONSE: inspect execution and stored artifacts; do not delete state or change filenames to force retry. Reconcile whether the request completed. Resume tooling is a later implementation, not an available command.

Current limits: text review only; no video/image byte inspection, source analysis author, GPT API automation, selection writer, trigger, deployment CI, media QC or render adapter. Do not label the entire workflow implemented from unit tests alone.

Run local tests: node --test workflow_v2/tests/google_native.test.cjs
