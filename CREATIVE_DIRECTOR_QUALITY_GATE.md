# The Little Days — AI Creative Director & Quality Gate

Status: PROPOSED INTEGRATION · 2026-10-31 · Does not authorize production, render, deployment, scheduling, or Sheet edits.

## Purpose and precedence

Insert two logical modules between verified source analysis and script/asset production. This document records the owner's newer instruction to compare GPT and Gemini ideas without assuming a Gemini rewrite is superior. It supersedes the older *unconditional Gemini-final-wins* rule **only for candidate selection**. A genuine Gemini review is still mandatory before a candidate can be marked quality-approved; all other ARCHITECTURE_LOCK.md requirements remain binding. This document defines candidate selection; runner stage validation exists but real AI workers are not yet connected.

## Flow

1. Existing intake: live Sheet row A (idea_id), B (source video); verified media/audio analysis, limitations and provenance. Do not infer video content from URL/thumbnail.
2. **AI Creative Director — GPT candidate:** using source observations and project brief, author a complete new idea (hook, setup, progression, payoff), performance and natural US English dialogue. Save as immutable `gpt_candidate_vN`; do not overwrite with Gemini output.
3. **Gemini independent critique:** send the actual minimal necessary evidence, GPT candidate and rubric to the real Gemini API. Require concrete weaknesses, line/scene references, severity, suggested repairs, transcript confidence and evidence gaps. Store the actual provider response and model metadata. Never simulate a Gemini review.
4. **Gemini rewrite:** save `gemini_candidate_vN` independently, preserving GPT version. Rewrite must address critique; if Gemini rejects or evidence is insufficient, record that status without inventing a rewrite.
5. **Quality Gate:** apply hard constraints and rubric to both candidates. Record score breakdown, evaluator identity, rationale, and uncertainty. The same model reviewing its own output is insufficient as the sole impartial evaluator: independent checks and owner calibration are required. Apply the same rubric to both versions; stronger score is not by itself proof of future virality or performance.
6. Select the higher-quality eligible version, **not automatically Gemini**. If neither clears the threshold, set `NEEDS_REVISION` / `INSUFFICIENT_EVIDENCE`; do not produce assets. Ties or material disagreements go to owner review. The selected idea awaits human approval before production, per the newest request.
7. Keep GPT and Gemini candidate text in separate columns C/D once quality-reviewed; after human approval, continue selected story into E/F/G and storyboard K. D/E/F must follow TOOL_INTAKE_WORKFLOW.md, preserving the approved story and exact approved text where relevant. Do not automatically submit to third-party tools.

## Hard constraints (fail closed)

- Source and audio adequately verified, or label `INSUFFICIENT_EVIDENCE`.
- Character Identity Lock: FATHER, MOTHER, DAUGHTER, DOG; M5 is the **single** image identity source for all four characters (not L6). A textual brief cannot substitute for viewing M5 at image creation time.
- Maintain stable identity, recognizable behavior/personality, plausible toddler speech, voice and episode-specific wardrobe continuity.
- Complete dialogue and acting time; never remove lines simply to fit a fixed duration. If duration exceeds tool capacity, plan multi-part Gemini video or ask permission before switching to Grok.
- No invented engagement metrics, unverifiable claims, fake model responses, fake job results, or hidden production.
- No automatic render, billing, publishing, admin-checkbox changes, or modifications to user inputs A/B.
- Unavailable Gemini review, ambiguous submission or source evidence: `PENDING_REVIEW` / `INSUFFICIENT_EVIDENCE`, never approved.

## Quality rubric (100 points, initial calibration proposal)

| Dimension | Points |
| --- | ---: |
| Comedic payoff and situational humor | 25 |
| Hook in first 3 seconds | 20 |
| Natural US English dialogue | 15 |
| Acting, expressions, body language | 15 |
| Timing and story coherence | 10 |
| Character fidelity and continuity | 10 |
| AI video production feasibility | 5 |

Proposed provisional threshold: >=85/100 **and** all hard constraints pass. 70–84 requires revision; <70 fails. Treat scoring as calibration, not an empirical guarantee of viewer reception. Preserve both candidates, scores and critique. A candidate cannot pass purely on arithmetic if a hard rule fails.

## Artifacts and states

Store private, versioned records keyed by `idea_id`, input SHA/hash and stage:
`source_evidence`, `gpt_candidate`, `gemini_critique_raw`, `gemini_candidate`, `quality_scores`, `selection_rationale`, `approval_status`, `next_action`, model/version, retry markers and error history.

States: `INPUT_READY` → `SOURCE_VERIFIED` → `GPT_DRAFTED` → `GEMINI_CRITIQUED` → `GEMINI_REWRITTEN` → `QUALITY_REVIEWED` → `READY_FOR_APPROVAL` → `APPROVED_FOR_SCRIPT`; blocked alternatives: `INSUFFICIENT_EVIDENCE`, `PENDING_REVIEW`, `NEEDS_REVISION`, `REJECTED`. Do not infer approvals from missing or false admin checkboxes; do not edit them.

The native Google Sheet v1.3 (ID `1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM`, tab `01_SAN_XUAT`) is the only interface. Keep separate GPT/Gemini drafts and scoring in versioned private artifacts first; do not add columns or overwrite any previously approved content. Sync to existing semantic fields **only after** header, row, input hash and owner-approval checks. Preserve formatting and admin cells. No Sheet layout changes are authorized.

## Orchestration, costs, retries

- GitHub is canonical for code; ChatGPT coordinates; GitHub Actions can trigger verified API steps. Gemini participates via genuine API; Google Drive stores reference media; local runner/browser is only for stages that need it.
- Reuse the existing daily 09:00 Asia/Bangkok input scan. **Do not create a second scan or schedule**. Until end-to-end coordinator wiring is tested, this module is specification only.
- Cache successful stage results by input hash + rubric/prompt version; don't reupload video or rescore unchanged work. Resume incomplete stages rather than restarting. Send Gemini compact packets, but provide actual video/audio when source validation requires it.
- Follow TOOL_INTAKE_WORKFLOW.md for transient review HTTP 500/502/503/504 retries and marker reconciliation; never copy review retries into render jobs. No unbounded loop and no automatic retry of ambiguous network submissions.
- Never store keys, source videos, runtime state, browser cookies or provider credentials in git.
- No code/deploy/render changes, existing IDEA_002 jobs, branch protections, or Sheet mutations are implied by this spec.

## Acceptance tests before enabling

1. GPT original and Gemini rewrite remain independently retrievable.
2. Critique identifies specific weaknesses and evidence, not generic praise.
3. Quality Gate can choose GPT over Gemini, Gemini over GPT, or neither.
4. Hard-constraint violation blocks even a numerically high-scoring idea.
5. Missing Gemini response or uncertain audio blocks approval.
6. Duplicate input/event never creates duplicate provider calls.
7. Existing Sheet cells and admin controls remain intact.
8. Owner approval is explicitly recorded before downstream creative production.
9. Quota/503 handling preserves submission intent and resume safety.
10. No render or publish actions occur in creative review tests.

## Owner decision lock — 2026-10-31

Quality Gate has a bounded decision cycle. Scores >=85/100 with all hard constraints satisfied qualify for owner idea review; 75-84 permits one targeted revision; below 75 requires rewrite or rejection. After at most TWO targeted revision rounds, output SELECT or REJECT, never another open-ended draft. Any blocking identity, dialogue or feasibility defect overrides the numeric score. SELECT means candidate for final QC, not permission to render: owner idea/script approval is still mandatory.

For IDEA_TEST, the owner-selected candidate for FINAL QC is v3.2, documented in 03_NHAT_KY_CHAY, not a replacement for separate GPT C5 and Gemini D5. Do not create v3.3 merely to rerun general review. Final QC must resolve audio attribution, identity M5 and shot feasibility and make an explicit pass/fail decision. Until then admin approvals remain false, production remains pending, and no render is authorized. Preserve source reports and all historical QC records. This decision updates the earlier provisional 70-84 band.

## Frame 0 & wardrobe policy — owner approved 2026-10-31

**Frame 0 is mandatory** after owner approval of storyboard and before any video generation. Do not bypass this step by submitting only the storyboard and M5 to a video tool. Frame 0 requires visual QC and owner confirmation before it can be used for rendering.

**M5 is identity reference ONLY, not a fixed wardrobe reference.** Lock face, age, body build, recognizable hairstyle, dog breed/fur and stable character identity. Clothing is designed per episode based on scene, time of day, weather, action, tone and story. Never mechanically copy M5 outfits. Once an episode wardrobe is chosen, keep it continuous across all frames/shots of that episode; change it only if the approved story explicitly calls for a costume change.

**Frame 0 acceptance:** all four characters recognizable as M5; contextually appropriate wardrobe; exact scene blocking, mood and 9:16 layout; appropriate body language; no added props/people; no continuity mistakes. Preserve the approved storyboard dialogue without shortening to force duration. Prompt language US English; idea descriptions/review in Vietnamese. Keep M5 unchanged.

**IDEA_TEST / GOOD BOY, DAD!:** morning doorway scene. Father comfortable casual morning clothes, Mother relaxed homewear, Daughter age-appropriate comfortable morning outfit; dress/garments should be intentionally different from M5 clothing, but their identity must match M5. Brown Dachshund retains blue collar. Frame 0 should show the beginning of Scene 1, before the father's goodbye action, with mother, toddler and dog all spatially coherent. Do not produce a Frame 0 or render merely because this policy was recorded.

## Series-wide Voice Identity Lock — owner directive, 2026-10-31

FATHER, MOTHER, DAUGHTER have distinct, stable voice identities across **all** episodes and all shots. Dog has no human speech unless a specific approved idea explicitly requires it. A per-prompt instruction such as "adult male voice" or "toddler voice" is NOT a verifiable voice lock.

Create an immutable **VOICE_REGISTRY** before production that contains for each speaking character: character_id, immutable voice_id/provider_voice_id (where available), approved voice sample asset reference and checksum, locale/accent (natural US English), vocal age/range, pitch/timbre/speaking rhythm, allowed emotion/prosody variation, voice_registry_version and owner approval. Keep samples private in Drive; never put voice audio, secrets or personal recordings in GitHub. If a provider cannot accept/reference a fixed voice ID or voice sample, mark voice_lock_verified=false and route to a controlled post-production voice/lip-sync pipeline or obtain owner approval for an exception. Never promise exact identical voices from prompt wording alone.

Speaker Lock: each script line gets unique utterance_id + character_id + exact dialogue + time budget. No assigning another character's line, no multi-character simultaneous lip-sync; nonspeaking characters do not mouth dialogue. Mother may LAUGH as nonverbal audio without becoming a dialogue speaker; use the same Mother voice identity for such vocalizations when possible. Never reassign the punchline "Good boy, Daddy!" away from DAUGHTER.

Quality Gate before render requires:
- Character identity M5 and approved Frame 0, outfit/scene continuity.
- Voice registry entries for all speaking characters (including Mother if she laughs), owner-approved samples/voice IDs and provider capability or a verified post-dub plan.
- Gemini independently critiques GPT's **video prompt** for speaker confusion, voice consistency, lip-sync, dog-kiss visibility, 10-second feasibility, final comedic beat, and absence of subtitles.
- Preserve GPT prompt and Gemini critique/rewrite separately; no assumption Gemini is superior. A missing verified voice-lock mechanism blocks production, not general prompt drafting.
