# Canonical Google Sheet switch — v1.3 (2026-10-31)

**New sole source of truth**: Google Sheet ID `1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM`, tab `01_SAN_XUAT`, headers row 4, data row 5 onward. Source established from owner's linked native Google Sheet, matched to supplied v1.3 workbook snapshot.

**Old Sheet ID `1MfErcyvRQSWS7kABIyq3_ljzI1keZ4HRl1Ngh3n-Cag` is deprecated.** Never scan, write, resume, or render from the old Sheet. Keep historical IDs in archival descriptions only, not executable configuration. The actual old Drive file is NOT deleted by this change.

## New 01_SAN_XUAT contract

A idea ID (owner); B source video (owner); C Idea GPT; D Idea Gemini; E Hook; F Insight; G Proposed Angle — US; H external tool idea ID; I owner approval idea; J selected hook; K script; L owner approval script; **M5 fixed canonical identity reference for all ideas**; N frame 0; O canonical prompt; P video provider; Q version; R stop point; S production state; T tool response; U video code; V owner final approval; W title; X hashtag; Y Instagram; Z Facebook; AA YouTube; AB TikTok; AC raw video; AD final video; AE overall video QC; AF execution record.

Other tabs: `00_HUONG_DAN`, `02_CAU_HINH`. Protect owner columns A/B/I/L/V and user choices P/R, preserve content and existing IDEA_TEST artifacts. Never assume image identity comes from L5 or L6; L is now the script approval column. Reference is **M5**.

## Migration safety

- Existing runner.py assumes the v0.1 schema (reference in L, idea in old C, script in old J, etc.). **Do not run old runner's plan/run/write against v1.3**; it would fail header validation or target wrong columns. The updated config is a declaration of target, not evidence of successful runtime migration.
- Update runner's stage contracts and tests for split GPT/Gemini candidates, approval controls and fixed M5 identity before enabling automation. Keep `workers={}` and disable any old-sheet scheduled scan until safe migration is verified.
- Review `WL.optimus.md`, `ARCHITECTURE_LOCK.md`, browser packet scripts, GitHub Actions, sheet syncing and task prompts; new v1.3 schema takes precedence over historic old-sheet column examples.
- No render, no billing, no Sheet edits, and no loss of old-sheet data. Require end-to-end pilot on IDEA_TEST first.
