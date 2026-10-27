# Tool intake fields and Gemini error recovery

This is the current supplemental procedure for the idea-review stage. Use it with WL.optimus.md. It supersedes generic D/E/F descriptions and the old unconditional no-retry rule for explicit transient review HTTP errors. It does not authorize third-party submission, video resubmission or publishing.

## Required intake stage
After the idea is approved and before script production, read the current headers and map:
- D: Idea / hook. A concrete self-contained pitch: hook, setup, progression and payoff. A generic question alone is insufficient.
- E: Deep insight / why people share. Explain the emotional tension, recognition and specific sharing motive. Do not substitute a generic developmental fact or promise virality.
- F: Original proposed angle. Explain the series-specific setting, cast roles, creative perspective and performance. A tool label saying 100% original is not a guarantee of uniqueness.

Keep the already approved core story. Write Vietnamese ready to paste into the intake tool, with US English only for example dialogue. Omit technical metadata, status labels and production disclaimers from these three fields.

Send the field requirements and approved idea to actual Gemini. Gemini may rewrite and has final editorial authority. Save the original review and final text privately. Write the approved wording verbatim into the existing semantic fields only after rechecking row ID, source, headers and validation. Re-read the values; preserve formatting, other fields and admin controls. Do not auto-submit to the third-party tool.

## Review API recovery
503 may indicate temporary service overload/unavailability. Capture the actual status and a key-redacted message; do not infer a key or quota problem from status alone.

The review client:
- Retries explicit HTTP 500/502/503/504 at most four total attempts.
- Uses approximately 5/10/20 seconds exponential backoff plus jitter.
- Honors numeric Retry-After up to 60 seconds. Stops on longer or unhandled values.
- Does not retry HTTP 400/401/403/404/429 automatically; no billing changes.
- Does not retry ambiguous network failures/timeouts automatically.
- Keeps submission-intent markers and saves raw responses before interpretation. Reconcile existing markers or saved responses before another invocation.
- Does not silently switch models or launch parallel review requests.
- Never applies these retries to video generation jobs.

When retries are exhausted, retain pending status and approved prior data; do not write unapproved replacements.

## Validation
Seven automated tests cover retry success, retry budget, quota stop, ambiguous network failures, key redaction and Retry-After behavior. A live review succeeded after the patch and returned an approved rewrite of the intake fields. This confirms a successful run, not permanent elimination of provider-side 503 responses.

This standalone review client is not yet wired into the scheduled coordinator or automatic sheet syncing.

Official guidance: https://ai.google.dev/gemini-api/docs/troubleshooting
