# Workflow V2 — approved M5 layout checkpoint (2026-10-31)

The owner chose to retain the current Sheet layout. Canonical identity is now
01_SAN_XUAT!M5, with the same Drive file and image SHA-256. L5 remains an owner
checkbox. Never move columns or write that checkbox to restore the old layout.

Mapping: C GPT, D Gemini, E Hook, F Insight, G US Angle, I/L/V admin, K script,
M reference, N frame, O prompt, P provider, Q revision, R stop, S status, AF manifest.

This independent read-only preflight consumes a connected Sheet snapshot:
spreadsheet_id, headers (row 4), rows (starting row 5), and settings (key/value map).
Run from repository root:

```text
python -m workflow_v2.layout --snapshot PATH_TO_PRIVATE_SNAPSHOT --idea IDEA_TEST
python -m unittest discover -s tests -p test_layout_m5.py
```

layout PASS checks the table binding only. It does not mean media was inspected,
Gemini reviewed, or production may start. Source audio and the actual Gemini
connection still need verification. No AI calls or Sheet writes occur in this tool.

The legacy config.pilot.json, pilot_workflow.py and runner.py remain bound to the
old layout. They are NOT migrated or authorized against this Sheet. Their strict
header checks must continue to reject it. Do not run the old packet preparation
or activate legacy workers against this layout. Deployment and render stay off.
Future V2 execution must consume this contract, verify media bytes and perform
the required GPT → Gemini critique/rewrite → compare sequence.

The Sheet guide/configuration is synchronized to M5; historical run logs preserve
the old reference and must not be retroactively rewritten. Changing the location
does not create or approve either idea candidate.
