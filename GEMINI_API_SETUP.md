# Gemini API idea review

Status: code prepared; no successful live review verified. Browser and extension are not required for this review client. This does not automate rendering or configure scheduled runs.

Create an API key in https://aistudio.google.com/apikey using the owner's account. Configure GEMINI_API_KEY locally using Windows Environment Variables (User variables). Never paste the key into chat, GitHub, Sheets or command history. Restart the Desktop Commander app after configuring environment variables. The client also checks the current user's Windows Environment registry without printing its value.

Run in the project folder:
```powershell
python gemini_idea_review.py --list-models
```
Choose an available generateContent model supporting video and JSON output; no model is silently selected. Verify billing and quota in AI Studio.

Prepare a UTF-8 JSON packet containing idea_id, source observations and limitations, candidate idea/hook/insight/angle, complete candidate script and the latest owner brief. Pass the actual source MP4 separately. Drive links alone do not replace video bytes.

```powershell
python gemini_idea_review.py --model MODEL_ID --packet idea002-review-v1.json --video IDEA_002.mp4 --output runtime/idea002-review-v1.json
```

The client caps inline video at 15 MB; larger inputs require a Files API implementation. Source is sent to Google for review. It writes a submission-intent marker before calling, raw provider response before validation, and a validated record with model, input hash and response ID when supplied. An interrupted or failed request is not automatically resubmitted: reconcile its pending marker first. It does not print the key or provider error body.

Only use or revise with replacement_approved=true may proceed, and all four final content fields must be nonempty. reject/insufficient_evidence remain blocked. Inspect transcript and limitations before marking the source verified. Preserve the actual Gemini final text when syncing to the correct existing Sheets row. This standalone client does not write Sheets or connect runner stages; those integrations remain unfinished.

Do not commit runtime records, source videos, API keys, environment files or credential files.

Official docs:
- https://ai.google.dev/gemini-api/docs/api-key
- https://ai.google.dev/gemini-api/docs/video-understanding
- https://ai.google.dev/gemini-api/docs/structured-output
