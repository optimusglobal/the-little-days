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

/**
 * Phase 5: audit the previously saved source-video review against the actual
 * M5 CHARACTER IMAGE and the live GPT/Gemini versions. One model call.
 * Stores a new immutable Drive JSON report; does NOT alter Sheet or approve.
 * The old video report is reused, so video is NOT uploaded again.
 */
function tldReviewIdentityAndQualityGate() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('Another TLD review is running');
  try {
    const sourceReportId = '1h0Sr8Eu1oQBDPQr95wfXtBsrcUl70bpf';
    const sheet = SpreadsheetApp.openById(TLD_SHEET_ID).getSheetByName(TLD_TAB);
    if (!sheet || sheet.getRange('A5').getDisplayValue().trim() !== 'IDEA_TEST')
      throw new Error('IDEA_TEST row has changed');
    const sourceLink = sheet.getRange('B5').getDisplayValue().trim();
    const gpt = sheet.getRange('C5').getDisplayValue().trim();
    const geminiOld = sheet.getRange('D5').getDisplayValue().trim();
    const identityUrl = sheet.getRange('M5').getDisplayValue().trim();
    if (!sourceLink || !gpt || !geminiOld || !identityUrl)
      throw new Error('Missing required B5/C5/D5/M5 data');
    const sourceMatch = sourceLink.match(/^https:\/\/drive\.google\.com\/file\/d\/([A-Za-z0-9_-]+)(?:\/|$)/);
    const identityMatch = identityUrl.match(/^https:\/\/drive\.google\.com\/file\/d\/([A-Za-z0-9_-]+)(?:\/|$)/);
    if (!sourceMatch || !identityMatch) throw new Error('Invalid Drive source/reference link');
    const record = JSON.parse(DriveApp.getFileById(sourceReportId).getBlob().getDataAsString('UTF-8'));
    if (record.schema !== 'TLD_GEMINI_SOURCE_REVIEW_V1' ||
        record.idea_id !== 'IDEA_TEST' ||
        record.source_drive_id !== sourceMatch[1] ||
        record.identity_image_visually_reviewed !== false ||
        !record.gemini_result?.visual_observations?.length)
      throw new Error('Source review evidence mismatch: stopped');
    const img = DriveApp.getFileById(identityMatch[1]);
    if (!['image/png','image/jpeg','image/webp'].includes(img.getMimeType()))
      throw new Error('M5 is not a supported image');
    if (!img.getSize() || img.getSize() > 6*1024*1024)
      throw new Error('M5 image too large');
    const imageBytes = img.getBlob().getBytes();
    const hash = value => Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value)
      .map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join('');
    const imageSha = hash(imageBytes);
    const ideaHash = hash(gpt+'\n---GEMINI---\n'+geminiOld);
    const props = PropertiesService.getScriptProperties();
    const cacheKey = 'TLD_ID_GATE_' + record.source_sha256.slice(0,12) +
      '_' + imageSha.slice(0,12) + '_' + ideaHash.slice(0,12);
    if (props.getProperty(cacheKey)) {
      console.log(JSON.stringify({status:'IDENTITY_QC_ALREADY_SAVED',
        report_file_id:props.getProperty(cacheKey),model_calls:0,sheet_writes:0}));
      return;
    }
    const key = props.getProperty('GEMINI_API_KEY');
    const model = props.getProperty('GEMINI_MODEL') || 'gemini-3.5-flash-lite';
    if (!key || !/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Invalid Gemini configuration');
    const prompt = [
      'Bạn là kiểm duyệt viên sáng tạo độc lập cho The Little Days.',
      'Quan sát ẢNH M5 ĐÍNH KÈM để xác minh nhận diện 4 nhân vật bố, mẹ, bé gái, chó.',
      'Báo cáo video B5 đính dưới đây là hồ sơ Gemini trước đó: KHÔNG phải video bạn được xem trong lượt này.',
      'Phân biệt dữ kiện nguồn và nhân vật series. Không thay chó M5 bằng chó trong video gốc.',
      'Phiên âm cũ do AI tự nhận là high confidence, KHÔNG được gọi là human verified.',
      'Phản biện nội dung GPT C5 và bản Gemini D5, phát hiện lỗi liên tục, đạo cụ tự thêm, nhịp diễn, tuổi bé.',
      'Trình bày BẰNG TIẾNG VIỆT, riêng lời thoại nhân vật viết US English tự nhiên.',
      'Tạo phiên bản Gemini cải tiến mới, giữ đầy đủ 4 nhân vật theo M5, không ép cắt thoại.',
      'Đánh giá mỗi phiên bản GPT và Gemini cũ theo 7 hạng mục trọng số: hài 25, hook 20,',
      'US English 15, diễn xuất 15, nhịp 10, nhận diện 10, khả thi 5.',
      'Nếu thiếu bằng chứng để phê duyệt, kết luận NEEDS_REVISION hoặc INSUFFICIENT_EVIDENCE.',
      'Không mặc định Gemini thắng và không tự phê duyệt hay render.',
      'JSON keys: identity_observations (array), source_vs_identity (array),',
      'audio_caveats (array), gpt_weaknesses (array), gemini_weaknesses (array),',
      'gemini_rewrite_v2 (string), gpt_score (object keys comedy,hook,english,acting,timing,identity,feasibility,total),',
      'gemini_old_score (same keys), recommended_version (GPT|GEMINI_OLD|NEITHER),',
      'gate_status (NEEDS_REVISION|INSUFFICIENT_EVIDENCE|READY_FOR_OWNER_REVIEW),',
      'rationale (string), limitations (array).',
      'HỒ SƠ PHÂN TÍCH VIDEO ĐÃ CÓ:\n'+JSON.stringify(record.gemini_result),
      'IDEA GPT C5:\n'+gpt,
      'IDEA GEMINI CŨ D5:\n'+geminiOld
    ].join('\n\n');
    const res = UrlFetchApp.fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/'+
      encodeURIComponent(model)+':generateContent', {
        method:'post',contentType:'application/json',
        headers:{'x-goog-api-key':key},
        payload:JSON.stringify({contents:[{role:'user',parts:[
          {text:prompt},{inlineData:{mimeType:img.getMimeType(),
            data:Utilities.base64Encode(imageBytes)}}
        ]}],generationConfig:{temperature:0.2,maxOutputTokens:5000,
          responseMimeType:'application/json'}}),
        muteHttpExceptions:true
      });
    if (res.getResponseCode() !== 200) {
      console.log(JSON.stringify({status:'IDENTITY_QC_HTTP_FAILED',
        code:res.getResponseCode(),model_calls:1,sheet_writes:0}));
      throw new Error('Gemini identity QC failed; do not retry blindly');
    }
    const api = JSON.parse(res.getContentText());
    const parts = (((api.candidates||[])[0]||{}).content||{}).parts||[];
    const review = JSON.parse(parts.map(x=>x.text||'').join(''));
    if (!Array.isArray(review.identity_observations) ||
        !Array.isArray(review.gpt_weaknesses) ||
        !Array.isArray(review.gemini_weaknesses) ||
        typeof review.gemini_rewrite_v2 !== 'string' ||
        review.gemini_rewrite_v2.length < 250 ||
        !['GPT','GEMINI_OLD','NEITHER'].includes(review.recommended_version) ||
        !['NEEDS_REVISION','INSUFFICIENT_EVIDENCE','READY_FOR_OWNER_REVIEW'].includes(review.gate_status))
      throw new Error('Invalid identity QC response; no output saved');
    if (sheet.getRange('C5').getDisplayValue().trim() !== gpt ||
        sheet.getRange('D5').getDisplayValue().trim() !== geminiOld ||
        sheet.getRange('M5').getDisplayValue().trim() !== identityUrl)
      throw new Error('Sheet input changed during QC; no output saved');
    const output = {
      schema:'TLD_IDENTITY_QC_V1',idea_id:'IDEA_TEST',
      recorded_at:new Date().toISOString(),source_report_id:sourceReportId,
      source_sha256:record.source_sha256,identity_drive_id:identityMatch[1],
      identity_sha256:imageSha,idea_pair_sha256:ideaHash,model:model,
      reference_m5_supplied_to_model:true,source_video_reused_as_evidence:true,
      source_video_resubmitted:false,approval:'NOT_APPROVED',
      sheet_writes:0,gemini_result:review
    };
    const file=DriveApp.createFile('TLD_IDEA_TEST_IDENTITY_QC_'+imageSha.slice(0,12)+
      '.json',JSON.stringify(output,null,2),'application/json');
    props.setProperty(cacheKey,file.getId());
    console.log(JSON.stringify({status:'IDENTITY_QC_SAVED',report_file_id:file.getId(),
      model_calls:1,sheet_writes:0,d5_preserved:true,
      gate_status:review.gate_status,recommended_version:review.recommended_version}));
  } finally { lock.releaseLock(); }
}

/**
 * Phase 6: separate AUDIO QC. The model receives the ORIGINAL MP4 bytes,
 * not a prior model's transcript. Its output is explicitly not human verified.
 * One call, cached by source hash. No Sheet changes, no production approvals.
 */
function tldRunAudioQcIdeaTest() {
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(1000)) throw new Error('Audio QC already in progress');
  try {
    const sh=SpreadsheetApp.openById(TLD_SHEET_ID).getSheetByName(TLD_TAB);
    if(!sh || sh.getRange('A5').getDisplayValue().trim()!=='IDEA_TEST')
      throw new Error('Unexpected idea row');
    const link=sh.getRange('B5').getDisplayValue().trim();
    const m=link.match(/^https:\/\/drive\.google\.com\/file\/d\/([A-Za-z0-9_-]+)(?:\/|$)/);
    if(!m) throw new Error('B5 is not a direct Drive file URL');
    const file=DriveApp.getFileById(m[1]);
    if(file.getMimeType()!=='video/mp4' || file.getSize()>8*1024*1024)
      throw new Error('MP4 missing, wrong MIME or too large for inline analysis');
    const bytes=file.getBlob().getBytes();
    const hash=Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,bytes)
      .map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join('');
    const props=PropertiesService.getScriptProperties();
    const model=props.getProperty('GEMINI_MODEL')||'gemini-3.5-flash-lite';
    const key=props.getProperty('GEMINI_API_KEY');
    if(!key || !/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Invalid API settings');
    const ck='TLD_AUDIO_QC_'+hash.slice(0,24)+'_'+model;
    const previous=props.getProperty(ck);
    if(previous){
      console.log(JSON.stringify({status:'AUDIO_QC_ALREADY_SAVED',
        report_file_id:previous,model_calls:0,sheet_writes:0}));
      return;
    }
    const prompt=[
      'Independent audio-focused transcription of the attached short video.',
      'LISTEN to audio rather than copying visual guesses or old AI logs.',
      'Return exact audible English speech in time order, with approximate start/end seconds.',
      'For each turn: speaker (FATHER/MOTHER/DAUGHTER/UNKNOWN), text,',
      'confidence 0..1, uncertain_words, evidence_note. Do not fabricate missing words.',
      'Check specifically whether utterances such as Papa, Oh you too, Him too,',
      'Okay Bye Papa are present; mark absent or uncertain when appropriate.',
      'List sound cues and unresolved overlaps, and whether a human review is needed.',
      'Explain uncertainty and remarks in Vietnamese. Transcribed dialogue stays English.',
      'Return JSON keys: turns (array of objects start_s,end_s,speaker,text,',
      'confidence,uncertain_words,evidence_note), sound_cues (array),',
      'unresolved_audio (array), suspected_omissions (array),',
      'needs_human_review (boolean), assessment_vi (string).',
      'This is AI audio QC, NOT independently verified ground truth.'
    ].join(' ');
    const resp=UrlFetchApp.fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/'+
      encodeURIComponent(model)+':generateContent',{
        method:'post',contentType:'application/json',
        headers:{'x-goog-api-key':key},
        payload:JSON.stringify({contents:[{role:'user',parts:[
          {text:prompt},{inlineData:{mimeType:'video/mp4',
            data:Utilities.base64Encode(bytes)}}
        ]}],generationConfig:{temperature:0,maxOutputTokens:2800,
          responseMimeType:'application/json'}}),muteHttpExceptions:true
      });
    if(resp.getResponseCode()!==200){
      console.log(JSON.stringify({status:'AUDIO_QC_FAILED',
        http_status:resp.getResponseCode(),model_calls:1,sheet_writes:0}));
      throw new Error('Audio QC Gemini HTTP error. No automatic retry');
    }
    const result=JSON.parse(resp.getContentText());
    const output=(((result.candidates||[])[0]||{}).content||{}).parts
      ?.map(p=>p.text||'').join('')||'';
    const parsed=JSON.parse(output);
    if(!Array.isArray(parsed.turns)||!Array.isArray(parsed.unresolved_audio)||
       typeof parsed.assessment_vi!=='string'||
       parsed.turns.some(t=>typeof t.text!=='string'||
          !['FATHER','MOTHER','DAUGHTER','UNKNOWN'].includes(t.speaker)))
      throw new Error('Invalid transcript. No file saved.');
    if(sh.getRange('B5').getDisplayValue().trim()!==link)
      throw new Error('Source changed during Audio QC');
    const record={schema:'TLD_AUDIO_QC_V1',idea_id:'IDEA_TEST',
      recorded_at:new Date().toISOString(),model:model,
      source_file_id:m[1],source_sha256:hash,
      transcript_status:'AI_TRANSCRIPTION_NOT_HUMAN_VERIFIED',
      approval:'NOT_APPROVED',quality_gate:'WAITING_FOR_AUDIO_REVIEW',
      audio_result:parsed};
    const out=DriveApp.createFile('TLD_IDEA_TEST_AUDIO_QC_'+hash.slice(0,12)+
      '.json',JSON.stringify(record,null,2),'application/json');
    props.setProperty(ck,out.getId());
    console.log(JSON.stringify({status:'AUDIO_QC_SAVED',
      report_file_id:out.getId(),turns:parsed.turns.length,
      needs_human_review:parsed.needs_human_review,
      model_calls:1,sheet_writes:0,quality_gate:'BLOCKED'}));
  }finally{lock.releaseLock();}
}

/**
 * Bounded Creative Quality Gate v1 (pure policy, no provider/API calls).
 * SELECT means candidate for OWNER REVIEW, never a render authorization.
 * Hard blockers fail closed. At revision >= 2, no further revisions allowed.
 */
function tldDecideBoundedQualityGate(input) {
  if (!input || !Number.isInteger(input.revisionRounds) ||
      input.revisionRounds < 0 || !Array.isArray(input.candidates))
    throw new Error('Invalid quality gate input');
  const maxRevisions=2;
  const eligible=input.candidates.filter(c=>
    c && ['GPT','GEMINI','V3_2'].includes(c.id) &&
    Number.isFinite(c.score) && c.score>=0 && c.score<=100 &&
    c.hardConstraintsPass===true && c.evidenceSufficient===true);
  const winner=eligible.sort((a,b)=>b.score-a.score)[0];
  if(winner && winner.score>=85) return {
    decision:'SELECT',candidate:winner.id,
    status:'READY_FOR_OWNER_REVIEW',renderAllowed:false,revisionAllowed:false
  };
  if(input.revisionRounds>=maxRevisions) return {
    decision:'REJECT',candidate:null,status:'REJECTED',
    renderAllowed:false,revisionAllowed:false
  };
  return {decision:'REVISE',candidate:null,status:'NEEDS_REVISION',
    renderAllowed:false,revisionAllowed:true,
    remainingRounds:maxRevisions-input.revisionRounds};
}
/** Local policy test: zero network calls and zero Sheet writes. */
function tldTestBoundedQualityGate() {
  const scenarios=[
    [{revisionRounds:0,candidates:[{id:'GPT',score:90,hardConstraintsPass:true,evidenceSufficient:true},
      {id:'GEMINI',score:86,hardConstraintsPass:true,evidenceSufficient:true}]},'SELECT','GPT'],
    [{revisionRounds:1,candidates:[{id:'GEMINI',score:98,hardConstraintsPass:false,evidenceSufficient:true}]},'REVISE',null],
    [{revisionRounds:2,candidates:[{id:'GPT',score:80,hardConstraintsPass:true,evidenceSufficient:true}]},'REJECT',null],
    [{revisionRounds:2,candidates:[{id:'V3_2',score:86,hardConstraintsPass:true,evidenceSufficient:true}]},'SELECT','V3_2'],
    [{revisionRounds:0,candidates:[{id:'GPT',score:99,hardConstraintsPass:true,evidenceSufficient:false}]},'REVISE',null]
  ];
  scenarios.forEach(([input,expected,id])=>{
    const actual=tldDecideBoundedQualityGate(input);
    if(actual.decision!==expected || actual.candidate!==id || actual.renderAllowed)
      throw new Error('QC scenario failed: '+expected);
  });
  console.log(JSON.stringify({status:'BOUNDED_QC_POLICY_OK',
    scenarios:scenarios.length,model_calls:0,sheet_writes:0,render_calls:0}));
}

/**
 * Read-only FINAL QC preflight for IDEA_TEST, tied to live Sheet and saved
 * evidence. This is not a scoring call and never modifies production state.
 */
function tldPreflightIdeaTestFinalQc() {
  const ss=SpreadsheetApp.openById(TLD_SHEET_ID);
  const sheet=ss.getSheetByName(TLD_TAB);
  const journal=ss.getSheetByName('03_NHAT_KY_CHAY');
  if(!sheet||!journal) throw new Error('Missing required sheet');
  const row=sheet.getRange('A5:AF5').getDisplayValues()[0];
  if(row[0]!=='IDEA_TEST') throw new Error('Expected IDEA_TEST at A5');
  const logs=journal.getRange('A5:L12').getDisplayValues();
  const decision=logs.find(r=>r[0]==='idea-test-owner-decision-lock-20261031');
  const policy=logs.find(r=>r[0]==='idea-test-final-qc-policy-20261031');
  if(!decision||!policy) throw new Error('Decision/policy log missing');
  if(!decision[10].includes('SELECTED_FOR_FINAL_QC') ||
     !policy[10].includes('SELECTED_FOR_FINAL_QC'))
    throw new Error('Final QC candidate log mismatch');
  const ids={
    source_report:'1h0Sr8Eu1oQBDPQr95wfXtBsrcUl70bpf',
    identity_report:'1sNnU5JkTUoBmSa8AaTBHh54yEte0z-8s',
    audio_report:'17yuEZ-nR5_PYJ1LHtMvueNCQeaOhO4Qo'
  };
  const reports={};
  Object.keys(ids).forEach(k=>{
    reports[k]=JSON.parse(DriveApp.getFileById(ids[k])
      .getBlob().getDataAsString('UTF-8'));
    if(reports[k].idea_id!=='IDEA_TEST') throw new Error('Mismatched '+k);
  });
  if(reports.source_report.source_sha256!==reports.identity_report.source_sha256 ||
     reports.source_report.source_sha256!==reports.audio_report.source_sha256)
    throw new Error('Source SHA mismatch across evidence');
  const source=String(row[1]).match(/\/file\/d\/([A-Za-z0-9_-]+)/);
  const identity=String(row[12]).match(/\/file\/d\/([A-Za-z0-9_-]+)/);
  if(!source||!identity||
     source[1]!==reports.source_report.source_drive_id||
     identity[1]!==reports.identity_report.identity_drive_id)
    throw new Error('Live Sheet inputs differ from stored evidence');
  const approvals={idea:row[8]==='TRUE',script:row[11]==='TRUE',final:row[21]==='TRUE'};
  if(approvals.idea||approvals.script||approvals.final)
    throw new Error('Admin approval has changed; manual reconciliation required');
  if(row[17]!=='Dừng trước render'||row[18]!=='Chờ QC')
    throw new Error('Unexpected stop point or production status');
  const result={
    status:'FINAL_QC_PREFLIGHT_BLOCKED',idea:'IDEA_TEST',
    candidate:'V3_2',source_evidence_matched:true,
    image_m5_evidence_matched:true,audio_ai_only:
      reports.audio_report.transcript_status==='AI_TRANSCRIPTION_NOT_HUMAN_VERIFIED',
    human_audio_verified:false,
    scored_final_candidate:false,
    candidate_owner_approved:false,
    render_allowed:false,model_calls:0,sheet_writes:0
  };
  console.log(JSON.stringify(result));
  return result;
}

/**
 * Real Gemini pre-render PROMPT QA; reads GPT V3 from journal L17.
 * Never approves render or writes source GPT/production cells.
 * VOICE_REGISTRY not yet provisioned: voice-lock readiness MUST be false.
 */
function tldGeminiReviewVideoPromptIdeaTest() {
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(1000)) throw new Error('Prompt QA already running');
  try {
    const ss=SpreadsheetApp.openById(TLD_SHEET_ID);
    const sh=ss.getSheetByName(TLD_TAB), lg=ss.getSheetByName('03_NHAT_KY_CHAY');
    if(!sh||!lg||sh.getRange('A5').getDisplayValue()!=='IDEA_TEST')
      throw new Error('IDEA_TEST not found');
    if(sh.getRange('I5').getValue()!==true||sh.getRange('L5').getValue()!==true)
      throw new Error('Idea and storyboard not both approved');
    if(!sh.getRange('M5').getDisplayValue()||!sh.getRange('N5').getDisplayValue())
      throw new Error('M5 identity or N5 Frame 0 missing');
    if(sh.getRange('R5').getDisplayValue()!=='Dừng trước render')
      throw new Error('Render safety stop changed');
    if(lg.getRange('A17').getDisplayValue()!=='idea-test-prompt-v3-for-gemini-qc')
      throw new Error('GPT prompt journal key mismatch');
    const gpt=lg.getRange('L17').getDisplayValue();
    if(!gpt.includes('STRICT SPEAKER LOCK')) throw new Error('GPT V3 candidate missing');
    const props=PropertiesService.getScriptProperties();
    const key=props.getProperty('GEMINI_API_KEY');
    const model=props.getProperty('GEMINI_MODEL')||'gemini-3.5-flash-lite';
    if(!key||!/^[A-Za-z0-9._-]+$/.test(model)) throw new Error('Invalid Gemini setup');
    const digest=Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,gpt)
      .map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join('');
    const ck='TLD_PROMPT_QA_'+digest.slice(0,24)+'_'+model;
    if(props.getProperty(ck)){
      console.log(JSON.stringify({status:'PROMPT_QA_ALREADY_SAVED',
        report_file_id:props.getProperty(ck),model_calls:0,sheet_writes:0}));
      return;
    }
    const instruction=[
      'Act as an independent quality auditor of the GPT VIDEO GENERATION PROMPT below.',
      'This is NOT a generated video. The images M5 and Frame 0 N5 are NOT attached;',
      'you may discuss image-lock instructions, not claim to have examined the actual images.',
      'The Little Days MUST keep immutable, owner-approved voice identities for FATHER, MOTHER,',
      'and DAUGHTER across ALL episodes. Generic voice descriptions are insufficient.',
      'No approved VOICE_REGISTRY, provider voice IDs, or voice samples are provided here.',
      'Therefore explicitly flag missing voice lock as a production blocker.',
      'Audit exact speaker ownership, lip sync, Mother laughter (nonverbal), 10-second feasibility,',
      'DOG kiss visibility, character and wardrobe continuity, no subtitles, and comedy payoff.',
      'Identify at least three concrete weaknesses with severity, impact and correction.',
      'Produce a fully rewritten ENGLISH prompt for a 10-second single clip ONLY if plausible;',
      'otherwise propose a safe duration and explain why. Do not silently remove essential dialogue.',
      'Vietnamese for analysis, English for video prompt and exact spoken dialogue.',
      'JSON keys: weaknesses (array of {issue,impact,fix,severity}),',
      'speaker_lock_findings (array), voice_lock_findings (array),',
      'ten_second_feasibility (string), proposed_prompt (string),',
      'decision (REVISE|READY_FOR_OWNER_REVIEW|REJECT_10S),',
      'production_blockers (array), rationale_vi (string).',
      'GPT PROMPT TO AUDIT:\n'+gpt
    ].join('\n');
    const res=UrlFetchApp.fetch('https://generativelanguage.googleapis.com/v1beta/models/'+
      encodeURIComponent(model)+':generateContent',{
        method:'post',contentType:'application/json',
        headers:{'x-goog-api-key':key},
        payload:JSON.stringify({contents:[{role:'user',parts:[{text:instruction}]}],
          generationConfig:{temperature:0.2,maxOutputTokens:4000,
            responseMimeType:'application/json'}}),muteHttpExceptions:true
      });
    if(res.getResponseCode()!==200){
      console.log(JSON.stringify({status:'PROMPT_QA_HTTP_FAILED',http_status:res.getResponseCode(),
        model_calls:1,sheet_writes:0}));
      throw new Error('Gemini prompt review failed; no automatic retries');
    }
    const response=JSON.parse(res.getContentText());
    const parts=(((response.candidates||[])[0]||{}).content||{}).parts||[];
    const parsed=JSON.parse(parts.map(p=>p.text||'').join(''));
    if(!Array.isArray(parsed.weaknesses)||parsed.weaknesses.length<3||
       !Array.isArray(parsed.production_blockers)||!Array.isArray(parsed.voice_lock_findings)||
       typeof parsed.proposed_prompt!=='string'||parsed.proposed_prompt.length<200||
       !['REVISE','READY_FOR_OWNER_REVIEW','REJECT_10S'].includes(parsed.decision))
      throw new Error('Incomplete QA result; no report saved');
    if(lg.getRange('L17').getDisplayValue()!==gpt)
      throw new Error('GPT prompt changed during QA; report not saved');
    const record={schema:'TLD_PROMPT_QA_V1',idea_id:'IDEA_TEST',model:model,
      reviewed_at:new Date().toISOString(),gpt_prompt_sha256:digest,
      gpt_prompt_journal:'03_NHAT_KY_CHAY!L17',
      voice_registry_configured:false,voice_lock_verified:false,
      render_allowed:false,owner_approved:false,
      gpt_prompt_preserved:true,gemini_review:parsed};
    const file=DriveApp.createFile('TLD_IDEA_TEST_PROMPT_QA_'+digest.slice(0,12)+'.json',
      JSON.stringify(record,null,2),'application/json');
    props.setProperty(ck,file.getId());
    console.log(JSON.stringify({status:'GEMINI_PROMPT_QA_SAVED',
      report_file_id:file.getId(),weaknesses:parsed.weaknesses.length,
      decision:parsed.decision,voice_lock_verified:false,
      model_calls:1,sheet_writes:0,render_allowed:false}));
  }finally{lock.releaseLock();}
}
