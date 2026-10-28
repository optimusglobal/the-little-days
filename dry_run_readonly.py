"""Read-only production dry-run. Never prepares browser, reserves ledger, or submits render."""
import argparse
import json
from pathlib import Path
from runner import Sheets, cell, resolve, plan
from production_guard import check_historical_lock, GuardError
from approval_guard import verify_approval
from timeline_guard import validate_timeline
from export_browser_packet import select_segment_prompt, drive_id

def inspect(idea, config_path='config.example.json', timeline_path=None):
    config=json.loads(Path(config_path).read_text(encoding='utf8'))
    data=Sheets(config).read()
    result={'idea_id':idea,'sheet':'PASS','L5':'BLOCK','historical_lock':'BLOCK',
            'timeline':'NOT_TESTED','approval':'NOT_TESTED','packet':'NOT_TESTED','render':'NEVER_SUBMITTED'}
    matching=[r for r in data['rows'] if cell(r,0)==idea]
    if len(matching)!=1:
        raise ValueError('Expected exactly one matching idea row')
    row=matching[0]
    reference=cell(data['rows'][0],11)
    frame=cell(row,resolve(data['headers'],config['headers']['frame']))
    result['L5']='PASS' if reference and drive_id(reference) else 'BLOCK'
    result['frame']='PASS' if frame and drive_id(frame) else 'BLOCK'
    result['production_status']=cell(row,resolve(data['headers'],'Trạng thái sản xuất'))
    try:
        check_historical_lock('.runtime/browser',idea)
        result['historical_lock']='CLEAR'
    except GuardError:
        result['historical_lock']='BLOCK'
    if timeline_path:
        timeline=json.loads(Path(timeline_path).read_text(encoding='utf8'))
        try:
            verify_approval(timeline,idea)
            result['approval']='PASS'
        except GuardError:
            result['approval']='BLOCK'
        script=cell(row,resolve(data['headers'],config['headers']['script']))
        master=cell(row,resolve(data['headers'],config['headers']['prompt']))
        result['timeline']='BLOCK'
        for segment in timeline.get('segments',[]):
            sid=segment['segment_id']
            prompt=select_segment_prompt(timeline,sid,master)
            packet={'script':script,'prompt':prompt,'segment_id':sid,'timeline':timeline}
            validate_timeline(packet)
        result['timeline']='PASS'
    result['decision']='NO_GO' # A dry-run cannot grant production permission.
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--idea',required=True)
    p.add_argument('--config',default='config.example.json')
    p.add_argument('--timeline')
    a=p.parse_args()
    print(json.dumps(inspect(a.idea,a.config,a.timeline),ensure_ascii=True,indent=2))

if __name__=='__main__':main()
