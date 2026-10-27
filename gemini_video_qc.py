"""Versioned Gemini video QC; never submits video generation jobs."""
import argparse,base64,hashlib,json,sys
from pathlib import Path
from urllib.request import urlopen
from gemini_idea_review import api,write

def approved(result):
    return (isinstance(result,dict) and result.get('verdict')=='ready'
            and result.get('expected_lines_present') is True
            and result.get('speaker_assignments_correct') is True
            and isinstance(result.get('actual_transcript'),list)
            and result.get('material_errors')==[] and result.get('extra_dialogue')==[])

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video',required=True);p.add_argument('--expectations',required=True)
    p.add_argument('--output',required=True);p.add_argument('--download-info')
    p.add_argument('--model',default='gemini-3-flash-preview')
    a=p.parse_args()
    video=Path(a.video);output=Path(a.output)
    if a.download_info and not video.exists():
        from urllib.parse import urlsplit
        info=json.loads(Path(a.download_info).read_text(encoding='utf-8-sig'))
        url=info['download_url']; host=urlsplit(url).hostname or ''
        if urlsplit(url).scheme!='https' or not host.endswith('.oaiusercontent.com'):
            raise ValueError('Only connector-issued HTTPS download URL accepted')
        with urlopen(url,timeout=120) as response: data=response.read(15_000_001)
        if len(data)>15_000_000 or b'ftyp' not in data[:64]: raise ValueError('Expected small MP4')
        video.parent.mkdir(parents=True,exist_ok=True);video.write_bytes(data)
    data=video.read_bytes()
    if len(data)>15_000_000: raise ValueError('Use Files API for larger input')
    expectations=json.loads(Path(a.expectations).read_text(encoding='utf-8-sig'))
    identity=hashlib.sha256(data+json.dumps(expectations,sort_keys=True).encode()+a.model.encode()).hexdigest()
    if output.exists():
        if json.loads(output.read_text(encoding='utf-8'))['input_sha256']!=identity:
            raise ValueError('Different input: preserve prior output')
        print('Existing QC retained');return
    pending=output.with_suffix('.pending.json')
    if pending.exists() or output.with_suffix('.response.json').exists():
        raise ValueError('Reconcile prior QC request before retry')
    write(pending,{'input_sha256':identity,'model':a.model,'status':'submission_intent'})
    instructions="""Inspect actual video AND audio. The expected script is a comparison target, not proof of what was generated.
Transcribe audible speech with timestamps and identify visible speaker, voice, and uncertainty independently.
Check exact required lines/order, correct speakers/lip sync, extra words, consistent identities/voices,
anatomy/props, readable acting and story continuity. Do not invent required words from expectations.
Return JSON object with verdict ready/revise/insufficient_evidence, actual_transcript array,
expected_lines_present boolean, speaker_assignments_correct boolean, extra_dialogue array,
material_errors array, minor_errors array, reasons. ready only when all required speech is heard,
correctly assigned, and no material errors. Do not claim character identity verified against an unseen reference."""
    raw=api('models/'+a.model+':generateContent',{'systemInstruction':{'parts':[{'text':instructions}]},
      'contents':[{'role':'user','parts':[{'inlineData':{'mimeType':'video/mp4','data':base64.b64encode(data).decode()}},
                   {'text':json.dumps(expectations,ensure_ascii=False)}]}],
      'generationConfig':{'responseMimeType':'application/json'}},error_log=output.with_suffix('.errors.json'))
    write(output.with_suffix('.response.json'),raw)
    candidate=raw.get('candidates',[{}])[0]
    if candidate.get('finishReason')!='STOP': raise ValueError('Incomplete provider response')
    result=json.loads(''.join(x.get('text','') for x in candidate.get('content',{}).get('parts',[]) if not x.get('thought')))
    if not isinstance(result,dict): raise ValueError('QC must be one object')
    record={'provider':'Gemini','model':a.model,'response_id':raw.get('responseId'),
            'input_sha256':identity,'approved':approved(result),'review':result}
    write(output,record);pending.unlink()
    print(json.dumps(record,ensure_ascii=True))
if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('QC stopped: '+type(exc).__name__,file=sys.stderr);sys.exit(2)
