const {test}=require('node:test');
const assert=require('node:assert/strict');
const {validateReview_}=require('../google_apps_script/Code.js');
const p={idea_id:'IDEA_TEST',input_hash:'abc'};
const ok={...p,idea_gemini:'Independent story',scope:'TEXT_ONLY',media_verified:false,weaknesses:[{beat:'ending',reason:'unclear',viewer_impact:'confusion',suggested_fix:'show reaction'}],no_material_weakness_reason:''};
test('accepts genuine structured critique and independent rewrite',()=>assert.equal(validateReview_(ok,p),ok));
for(const [name,patch] of Object.entries({wrong_id:{idea_id:'OTHER'},stale_hash:{input_hash:'old'},missing_rewrite:{idea_gemini:''},fake_media:{media_verified:true},empty_critique:{weaknesses:[]},incomplete_weakness:{weaknesses:[{beat:'end'}]}})) test(name,()=>assert.throws(()=>validateReview_({...ok,...patch},p)));
test('allows justified absence of material flaws',()=>assert.ok(validateReview_({...ok,weaknesses:[],no_material_weakness_reason:'Setup and payoff are coherent; execution risk remains.'},p)));
const vm=require('node:vm'),fs=require('node:fs'),crypto=require('node:crypto');
function harness(status=200) {
 const data=['IDEA_TEST','Verified source synopsis','GPT original','','','',''];
 const props=new Map(Object.entries({TLD_SHEET_ID:'test',TLD_TAB:'pilot',TLD_FOLDER_ID:'folder',TLD_MODEL:'gemini-test',TLD_ENABLED:'true',GEMINI_API_KEY:'test-only'}));
 const files=new Map(); let calls=0;
 const range=(row,col,n,w)=>({getDisplayValues:()=>[row===1?['idea_id','source_analysis','idea_gpt','idea_gemini','review_link','state','input_hash']:data.slice(col-1,col-1+w)],setValue:v=>{data[col-1]=v;},setValues:vs=>vs[0].forEach((v,i)=>data[col-1+i]=v)});
 const ctx={console:{log:()=>{}},PropertiesService:{getScriptProperties:()=>({getProperty:k=>props.get(k),setProperty:(k,v)=>props.set(k,v)})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{}})},SpreadsheetApp:{openById:()=>({getSheetByName:()=>({getRange:range})}),flush:()=>{}},DriveApp:{getFolderById:()=>({createFile:(name,text)=>{const id='f'+files.size; files.set(id,text); return {getId:()=>id,getUrl:()=>id};}}),getFileById:id=>({getBlob:()=>({getDataAsString:()=>files.get(id)})})},MimeType:{PLAIN_TEXT:'text/plain'},Utilities:{DigestAlgorithm:{SHA_256:1},computeDigest:(_,v)=>[...crypto.createHash('sha256').update(v).digest()]},UrlFetchApp:{fetch:(_,req)=>{calls++;const packet=JSON.parse(JSON.parse(req.payload).contents[0].parts[0].text);return {getResponseCode:()=>status,getContentText:()=>JSON.stringify({responseId:'real-fixture',candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({...ok,idea_id:packet.idea_id,input_hash:packet.input_hash})}]}}]})};}}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../google_apps_script/Code.js'),'utf8'),ctx);
 return {ctx,data,props,files,calls:()=>calls};
}
test('repeat uses persisted response; preserves GPT; writes independent Gemini',()=>{const h=harness();assert.equal(h.ctx.runPilot().state,'WAITING_GPT_SELECTION');assert.equal(h.data[2],'GPT original');assert.equal(h.data[3],'Independent story');assert.equal(h.ctx.runPilot().state,'CACHE_HIT');assert.equal(h.calls(),1);assert.equal(h.files.size,2);});
for(const [status,state] of [[429,'WAITING_QUOTA'],[503,'WAITING_SERVICE'],[400,'HTTP_ERROR']]) test('HTTP '+status+' does not resubmit on restart',()=>{const h=harness(status);assert.equal(h.ctx.runPilot().state,state);assert.equal(h.ctx.runPilot().state,state);assert.equal(h.calls(),1);});
test('changed GPT cannot overwrite previous revision',()=>{const h=harness();h.ctx.runPilot();h.data[2]='Changed GPT';assert.equal(h.ctx.runPilot().state,'NEEDS_REVISION_RECONCILIATION');assert.equal(h.calls(),1);});
test('disabled installation makes no calls or writes',()=>{const h=harness();h.props.set('TLD_ENABLED','false');assert.equal(h.ctx.runPilot().state,'DISABLED');assert.equal(h.calls(),0);assert.equal(h.data[5],'');});
