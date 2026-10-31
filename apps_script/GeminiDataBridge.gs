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
