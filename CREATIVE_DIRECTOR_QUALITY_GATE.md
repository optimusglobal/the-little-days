# The Little Days — AI Creative Director & Quality Gate

Status: PROPOSED INTEGRATION · 2026-10-31 · Does not authorize production, render, deployment, scheduling, or Sheet edits.

## Purpose and precedence

Insert two logical modules between verified source analysis and script/asset production. This document records the owner's newer instruction to compare GPT and Gemini ideas without assuming a Gemini rewrite is superior. It supersedes the older *unconditional Gemini-final-wins* rule **only for candidate selection**. A genuine Gemini review is still mandatory before a candidate can be marked quality-approved; all other ARCHITECTURE_LOCK.md requirements remain binding. This document is not evidence of an implemented API integration.

## Flow

1. Existing intake: live Sheet row A (idea_id), B (source video); verified media/audio analysis, limitations and provenance. Do not infer video content from URL/thumbnail.
2. **AI Creative Director — GPT candidate:** using source observations and project brief, author a complete new idea (hook, setup, progression, payoff), performance and natural US English dialogue. Save as immutable `gpt_candidate_vN`; do not overwrite with Gemini output.
3. **Gemini independent critique:** send the actual minimal necessary evidence, GPT candidate and rubric to the real Gemini API. Require concrete weaknesses, line/scene references, severity, suggested repairs, transcript confidence and evidence gaps. Store the actual provider response and model metadata. Never simulate a Gemini review.
4. **Gemini rewrite:** save `gemini_candidate_vN` independently, preserving GPT version. Rewrite must address critique; if Gemini rejects or evidence is insufficient, record that status without inventing a rewrite.
5. **Quality Gate:** apply hard constraints and rubric to both candidates. Record score breakdown, evaluator identity, rationale, and uncertainty. The same model reviewing its own output is insufficient as the sole impartial evaluator: independent checks and owner calibration are required. Apply the same rubric to both versions; stronger score is not by itself proof of future virality or performance.
6. Select the higher-quality eligible version, **not automatically Gemini**. If neither clears the threshold, set `NEEDS_REVISION` / `INSUFFICIENT_EVIDENCE`; do not produce assets. Ties or material disagreements go to owner review. The selected idea awaits human approval before production, per the newest request.
7. Only after approval, map selected content into existing Sheet semantic columns C/D/E/F and continue intake/storyboard. D/E/F must follow TOOL_INTAKE_WORKFLOW.md, preserving the approved story and exact approved text where relevant. Do not automatically submit to third-party tools.

## Hard constraints (fail closed)

- Source and audio adequately verified, or label `INSUFFICIENT_EVIDENCE`.
- Character Identity Lock: FATHER, MOTHER, DAUGHTER, DOG; L5 is the **single** image identity source for all four characters (not L6). A textual brief cannot substitute for viewing L5 at image creation time.
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

The existing Sheet `01_SAN_XUAT` is the interface. Keep separate GPT/Gemini drafts and scoring in versioned private artifacts first; do not add columns or overwrite any previously approved content. Sync to existing semantic fields **only after** header, row, input hash and owner-approval checks. Preserve formatting and admin cells. No Sheet layout changes are authorized.

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
