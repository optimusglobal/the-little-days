# Offline idea review preparation

Run from the repository root, on the feature branch:

```powershell
python tools/prepare_idea_review.py --idea IDEA_TEST --snapshot .runtime/idea_test/sheet.snapshot.json --source-file "C:\Users\Admin\Downloads\idea test.mp4" --reference-file .runtime/idea_test/L5_canonical.png
```

Without --snapshot, the command reads the live Sheet using existing Application Default Credentials. It never writes the Sheet, activates workers, renders, or calls an AI provider. A connector snapshot is an explicitly captured input, not continuous synchronization; capture it again after any Sheet change.

The local source must be the downloaded file from column B; the operator/adapter must retain its download provenance. The packet records its actual SHA-256. The canonical L5 bytes are checked against the configured reference hash. The packet binds source bytes, L5 bytes, GPT draft and row revision; old packets remain in separate version folders. Repeating unchanged preparation checks every saved artifact hash before reuse.

Outputs: source.mp4, L5_canonical.png, sampled contact.png (1 fps; a contact sheet does not verify audio), a US-English Gemini review prompt and packet.json with media metadata and explicit pending-review limitations. The program does not inspect semantic audio content.

Next integration boundary: submit the video, L5 and prompt through a supported Gemini integration, capture the actual response/conversation evidence, then verify the current Sheet inputs before writing a complete Gemini idea to D. This command intentionally cannot claim review completion or write a verdict. No Gemini browser adapter is commissioned. Do not use terminal-driven browser control to bypass a blocked integration.

Quota: this command performs deterministic local work and makes zero AI requests. It does not remove the model usage required to author an idea or perform an actual Gemini review. Savings require before/after measurements; no percentage is asserted.
