/**
 * The Little Days v1.3 — Gemini Data Bridge.
 * Phase 1: strictly READ ONLY; no Gemini calls, no writes, no triggers.
 * Keep source code in GitHub; paste/deploy an audited revision to bound Apps Script.
 */
const TLD_SHEET_ID = '1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM';
const TLD_TAB = '01_SAN_XUAT';
const TLD_EXPECTED_HEADERS = {
  A: 'Mã idea nội bộ', B: 'Link video gốc',
  C: 'Idea GPT', D: 'Idea Gemini', M: 'Ảnh tham chiếu'
};
function tldTestReadOnly() {
  const key = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!key || !key.trim()) throw new Error('GEMINI_API_KEY missing from Script Properties');
  const ss = SpreadsheetApp.openById(TLD_SHEET_ID);
  const sheet = ss.getSheetByName(TLD_TAB);
  if (!sheet) throw new Error('Missing tab: ' + TLD_TAB);
  const headers = sheet.getRange('A4:M4').getDisplayValues()[0];
  const columnIndex = {A: 0, B: 1, C: 2, D: 3, M: 12};
  Object.entries(TLD_EXPECTED_HEADERS).forEach(([column, expected]) => {
    if (headers[columnIndex[column]] !== expected)
      throw new Error('Header changed at ' + column);
  });
  const id = String(sheet.getRange('A5').getDisplayValue()).trim();
  if (id !== 'IDEA_TEST') throw new Error('A5 is not IDEA_TEST; stopped');
  const video = String(sheet.getRange('B5').getDisplayValue()).trim();
  const gpt = String(sheet.getRange('C5').getDisplayValue()).trim();
  const gemini = String(sheet.getRange('D5').getDisplayValue()).trim();
  const identity = String(sheet.getRange('M5').getDisplayValue()).trim();
  if (!video || !identity) throw new Error('Missing source B5 or identity M5');
  // Log only presence/length, never links, text, private media, or credentials.
  console.log(JSON.stringify({
    status: 'READ_ONLY_OK', idea: id,
    source_link_present: true,
    gpt_idea_characters: gpt.length,
    gemini_idea_characters: gemini.length,
    character_reference_present: true,
    gemini_key_configured: true,
    writes: 0, model_calls: 0
  }));
}

/**
 * Phase 2: one low-cost real Gemini API connection test.
 * Does NOT submit idea/video, write cells, or create triggers.
 * Configure GEMINI_MODEL in Script Properties to override the default.
 */
function tldTestGeminiApi() {
  tldTestReadOnly();
  const props = PropertiesService.getScriptProperties();
  const key = props.getProperty('GEMINI_API_KEY');
  const model = props.getProperty('GEMINI_MODEL') || 'gemini-3.5-flash-lite';
  if (!/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Invalid GEMINI_MODEL');
  const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' +
    encodeURIComponent(model) + ':generateContent';
  const payload = {
    contents: [{role: 'user', parts: [{text:
      'Connectivity test only. Reply with exactly: TLD_GEMINI_OK'
    }]}],
    generationConfig: {maxOutputTokens: 64, temperature: 0}
  };
  const response = UrlFetchApp.fetch(endpoint, {
    method: 'post',
    contentType: 'application/json',
    headers: {'x-goog-api-key': key},
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
  const status = response.getResponseCode();
  if (status !== 200) {
    // Avoid logging response body or secrets.
    console.log(JSON.stringify({status: 'GEMINI_API_FAILED', http_status: status, model: model}));
    throw new Error('Gemini API connection failed; HTTP ' + status);
  }
  const body = JSON.parse(response.getContentText());
  const parts = ((body.candidates || [])[0] || {}).content?.parts || [];
  const text = parts.map(part => part.text || '').join('').trim();
  if (!text.includes('TLD_GEMINI_OK')) throw new Error('Gemini returned an unexpected response');
  console.log(JSON.stringify({
    status: 'GEMINI_API_OK',
    model: model,
    returned_marker: true,
    writes: 0,
    model_calls: 1
  }));
}

/**
 * Phase 3: one Gemini critique and independent rewrite for IDEA_TEST.
 * This step DOES NOT read video bytes or verify audio. It only checks GPT
 * against its stated video observations; no quality approval, no render.
 * Run manually once. Never overwrite an existing Gemini draft.
 */
function tldReviewIdeaTest() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('Review already running');
  try {
    const sheet = SpreadsheetApp.openById(TLD_SHEET_ID).getSheetByName(TLD_TAB);
    if (!sheet || sheet.getRange('A5').getDisplayValue().trim() !== 'IDEA_TEST')
      throw new Error('Wrong sheet or idea; stopped');
    const gpt = sheet.getRange('C5').getDisplayValue().trim();
    const previousGemini = sheet.getRange('D5').getDisplayValue().trim();
    if (previousGemini) {
      console.log(JSON.stringify({status:'SKIPPED_D5_ALREADY_FILLED', writes:0, model_calls:0}));
      return;
    }
    if (!gpt) throw new Error('C5 is empty. No review possible');
    const props = PropertiesService.getScriptProperties();
    const key = props.getProperty('GEMINI_API_KEY');
    if (!key) throw new Error('Missing GEMINI_API_KEY');
    const model = props.getProperty('GEMINI_MODEL') || 'gemini-3.5-flash-lite';
    if (!/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Invalid model');
    const prompt = [
      'You are an INDEPENDENT comedy script critic and rewriting editor for The Little Days.',
      'Audience: US viewers; natural US English. Four fixed characters: FATHER, MOTHER, DAUGHTER (age ~2), DOG.',
      'Do not claim you saw the source video or heard audio. You have ONLY a GPT text idea below.',
      'Provide 3 concrete weaknesses with references to lines, beats or actions, why they hurt comedy or feasibility, and fixes.',
      'Then write a distinctly improved, complete and filmable alternative with an immediate hook, clear setup and payoff.',
      'Keep toddler acting/speech age-appropriate; retain all four characters and visual identity reference M5.',
      'Do not invent source-video transcript, engagement metrics, or extra characters.',
      'Return JSON with: weaknesses (array of {issue,impact,fix}), rewritten_idea (string), caveats (string).',
      'Here is the GPT candidate:\n' + gpt
    ].join('\n');
    const url = 'https://generativelanguage.googleapis.com/v1beta/models/' +
      encodeURIComponent(model) + ':generateContent';
    const payload = {
      contents:[{role:'user',parts:[{text:prompt}]}],
      generationConfig:{temperature:0.45,maxOutputTokens:3000,
        responseMimeType:'application/json'}
    };
    const res = UrlFetchApp.fetch(url,{
      method:'post',contentType:'application/json',
      headers:{'x-goog-api-key':key},payload:JSON.stringify(payload),
      muteHttpExceptions:true
    });
    const status = res.getResponseCode();
    if (status !== 200) {
      console.log(JSON.stringify({status:'GEMINI_REVIEW_FAILED',http_status:status,model:model,writes:0}));
      throw new Error('Gemini API returned HTTP ' + status);
    }
    const api = JSON.parse(res.getContentText());
    const responseText = (((api.candidates||[])[0]||{}).content||{}).parts?.map(p=>p.text||'').join('')||'';
    const parsed = JSON.parse(responseText);
    if (!Array.isArray(parsed.weaknesses) || parsed.weaknesses.length < 3 ||
        !parsed.weaknesses.every(w=>w.issue && w.impact && w.fix) ||
        typeof parsed.rewritten_idea !== 'string' || parsed.rewritten_idea.trim().length < 300) {
      throw new Error('Incomplete review. No Sheet write performed');
    }
    // Recheck contents immediately before writing (no destructive overwrite).
    if (sheet.getRange('C5').getDisplayValue().trim() !== gpt ||
        sheet.getRange('D5').getDisplayValue().trim()) {
      throw new Error('C5/D5 changed during review. No write performed');
    }
    const critique = parsed.weaknesses.map((w,i)=>
      (i+1)+'. '+w.issue+' | Impact: '+w.impact+' | Fix: '+w.fix).join('\n');
    const draft = 'GEMINI CANDIDATE v1 — TEXT-ONLY REVIEW; VIDEO/AUDIO NOT VERIFIED\n\n' +
      parsed.rewritten_idea.trim() + '\n\nCRITIQUE OF GPT VERSION:\n' +
      critique + '\n\nLIMITATIONS: ' + (parsed.caveats || 'Source video/audio not independently verified.');
    // Only touch D5; preserve T5 existing notes and admin/production columns.
    sheet.getRange('D5').setValue(draft);
    console.log(JSON.stringify({status:'GEMINI_REVIEW_SAVED_D5',
      model:model,weaknesses:parsed.weaknesses.length,writes:1,model_calls:1,
      text_only:true,quality_gate:'NOT_RUN'}));
  } finally {
    lock.releaseLock();
  }
}

/**
 * Phase 4: independent review grounded in REAL source-video bytes + GPT C5.
 * Never overwrites D5 or any admin cells. Stores a versioned JSON evidence
 * report in Google Drive. One model call if no completed checkpoint exists.
 *
 * Use tldReviewIdeaTestWithVideo() manually for IDEA_TEST.
 */
function tldReviewIdeaTestWithVideo() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('Video review already running');
  try {
    const sheet = SpreadsheetApp.openById(TLD_SHEET_ID).getSheetByName(TLD_TAB);
    if (!sheet || sheet.getRange('A5').getDisplayValue().trim() !== 'IDEA_TEST')
      throw new Error('IDEA_TEST is not in A5');
    const source = sheet.getRange('B5').getDisplayValue().trim();
    const gpt = sheet.getRange('C5').getDisplayValue().trim();
    const identity = sheet.getRange('M5').getDisplayValue().trim();
    if (!gpt || !source || !identity) throw new Error('B5/C5/M5 must be populated');
    const match = source.match(/^https:\/\/drive\.google\.com\/file\/d\/([A-Za-z0-9_-]+)(?:\/|$)/);
    if (!match) throw new Error('B5 must be a direct Google Drive file link');
    const file = DriveApp.getFileById(match[1]);
    if (file.getMimeType() !== 'video/mp4')
      throw new Error('Only verified MP4 sources are supported for this test');
    const size = file.getSize();
    // inlineData increases base64 payload; keep API request well under 20 MB
    if (!size || size > 8 * 1024 * 1024)
      throw new Error('Video too large for inline review: use Files API for larger files');
    const blob = file.getBlob();
    const bytes = blob.getBytes();
    const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes);
    const sha = digest.map(b => ('0' + ((b + 256) % 256).toString(16)).slice(-2)).join('');
    const props = PropertiesService.getScriptProperties();
    const model = props.getProperty('GEMINI_MODEL') || 'gemini-3.5-flash-lite';
    const key = props.getProperty('GEMINI_API_KEY');
    if (!key || !/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Missing key or invalid model');
    const gptHash = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, gpt)
      .map(b => ('0' + ((b + 256) % 256).toString(16)).slice(-2)).join('');
    const cacheKey = 'TLD_VIDEO_REVIEW_' + sha.slice(0,16) + '_' + gptHash.slice(0,16);
    const existing = props.getProperty(cacheKey);
    if (existing) {
      console.log(JSON.stringify({status:'VIDEO_REVIEW_ALREADY_SAVED',
        report_file_id:existing, model_calls:0, sheet_writes:0}));
      return;
    }
    const instruction = [
      'You are an independent US-family-comedy creative editor.',
      'First WATCH and LISTEN to the attached original MP4 (video + audio).',
      'Then critique the GPT adaptation below, identify at least three concrete weaknesses,',
      'and rewrite a distinct, more effective idea while preserving the source premise.',
      'No invented dialogue: explicitly distinguish verified audible speech from uncertain audio.',
      'Four characters FATHER, MOTHER, DAUGHTER age about 2, DOG.',
      'Character reference M5 exists but its image is NOT supplied in this call;',
      'do NOT claim that you visually verified exact character appearance.',
      'Do not add unrelated props or change the physical positions without justification.',
      'Write observations, critique, and rewritten idea in VIETNAMESE.',
      'Only any actual proposed character DIALOGUE or generation PROMPTS should be US English.',
      'Return JSON keys: visual_observations (array), audio_observations (array),',
      'audio_confidence (high|medium|low), weaknesses (array of objects issue,impact,fix),',
      'rewritten_idea (string), source_fidelity_notes (array), limitations (array).',
      'GPT IDEA FROM C5:\n' + gpt
    ].join('\n');
    const payload = {
      contents:[{role:'user',parts:[
        {text:instruction},
        {inlineData:{mimeType:'video/mp4',data:Utilities.base64Encode(bytes)}}
      ]}],
      generationConfig:{temperature:0.3,maxOutputTokens:3500,responseMimeType:'application/json'}
    };
    const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' +
      encodeURIComponent(model) + ':generateContent';
    const res = UrlFetchApp.fetch(endpoint,{
      method:'post',contentType:'application/json',
      headers:{'x-goog-api-key':key},payload:JSON.stringify(payload),
      muteHttpExceptions:true
    });
    if (res.getResponseCode() !== 200) {
      console.log(JSON.stringify({status:'VIDEO_REVIEW_HTTP_ERROR',
        http_status:res.getResponseCode(),model:model,sheet_writes:0}));
      throw new Error('Gemini media review failed; no automatic retry');
    }
    const answer = JSON.parse(res.getContentText());
    const output = (((answer.candidates||[])[0]||{}).content||{}).parts
      ?.map(p=>p.text||'').join('')||'';
    const review = JSON.parse(output);
    if (!Array.isArray(review.visual_observations) ||
        !Array.isArray(review.audio_observations) ||
        !Array.isArray(review.weaknesses) || review.weaknesses.length < 3 ||
        !review.weaknesses.every(w=>w.issue && w.impact && w.fix) ||
        !['high','medium','low'].includes(review.audio_confidence) ||
        typeof review.rewritten_idea !== 'string' || review.rewritten_idea.length < 300)
      throw new Error('Incomplete Gemini media response; no record saved');
    if (sheet.getRange('B5').getDisplayValue().trim() !== source ||
        sheet.getRange('C5').getDisplayValue().trim() !== gpt ||
        sheet.getRange('M5').getDisplayValue().trim() !== identity)
      throw new Error('Input changed while reviewing; no record saved');
    const record = {
      schema:'TLD_GEMINI_SOURCE_REVIEW_V1',idea_id:'IDEA_TEST',
      recorded_at:new Date().toISOString(),model:model,
      source_drive_id:match[1],source_sha256:sha,source_size_bytes:size,
      gpt_sha256:gptHash,identity_reference_cell:'M5',
      identity_image_visually_reviewed:false,
      audio_verification:'model_reported_not_human_verified',
      approval:'NOT_APPROVED',quality_gate:'NOT_RUN',
      gemini_result:review
    };
    const name = 'TLD_IDEA_TEST_GEMINI_VIDEO_REVIEW_' + sha.slice(0,12) + '.json';
    // Create standalone evidence file rather than overwrite current D5/T5/AF5.
    const out = DriveApp.createFile(name,JSON.stringify(record,null,2),'application/json');
    props.setProperty(cacheKey,out.getId());
    console.log(JSON.stringify({status:'GEMINI_VIDEO_REVIEW_SAVED',
      report_file_id:out.getId(),model:model,source_bytes:size,
      weaknesses:review.weaknesses.length,
      audio_confidence:review.audio_confidence,model_calls:1,sheet_writes:0,
      d5_preserved:true,quality_gate:'NOT_RUN'}));
  } finally { lock.releaseLock(); }
}
