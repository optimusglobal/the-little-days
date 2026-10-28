"""Automatic local rendering from an already prepared sheet row; not an AI author."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from browser_video import Blocked, Job, MCP, lock
from production_guard import GuardError, check_timeline, reserve_submission, check_production_status
from export_browser_packet import verify_packet_live


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--idea', required=True)
    ap.add_argument('--packet', help='Use an already exported, verified packet')
    ap.add_argument('--model', default='Argon')
    ap.add_argument('--conversation', help='Explicitly recover an existing Gemini result, never submit again')
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--send-confirmed', action='store_true')
    ap.add_argument('--revision-approved', action='store_true')
    ap.add_argument('--runtime', default=os.environ.get('WL_BROWSER_RUNTIME','.runtime/browser'))
    ap.add_argument('--output', default=str(Path.home()/'Videos'/'TheLittleDays'))
    args=ap.parse_args()
    if args.packet:
        packet_path=Path(args.packet)
    else:
        process=subprocess.run([sys.executable,'export_browser_packet.py','--idea',args.idea,'--model',args.model],
                               capture_output=True,text=True,encoding='utf-8')
        if process.returncode:
            raise Blocked('Sheet/Drive export failed; check local Google credentials and sharing')
        packet_path=Path(json.loads(process.stdout)['packet'])
    packet=json.loads(packet_path.read_text(encoding='utf-8'))
    if not packet.get('segment_id') or not isinstance(packet['segment_id'], str):
        raise Blocked('Packet must contain a stable segment_id')
    if packet['idea_id'] != args.idea:
        raise Blocked('Packet idea ID differs from requested idea')
    job=Job(packet,args.runtime,MCP())
    with lock(job.folder):
        if job.state['status']=='downloaded':
            job.download(Path.home()/'Downloads',args.output)
        elif args.conversation:
            job.adopt(args.conversation)
        elif job.state['status'] in ('new','awaiting_extension_file_permission'):
            job.prepare()
        if args.prepare_only:
            print(json.dumps({'status':job.state['status'],'record':str(job.path)}))
            return
        if job.state['status']=='prepared':
            if not args.send_confirmed:
                raise Blocked('Prepared only; --send-confirmed required for render')
            try:
                verify_packet_live(packet)
                check_production_status(packet.get('production_status',''))
                check_timeline(packet.get('script', ''), packet['prompt'])
                reserve_submission(Path(args.runtime), args.idea, packet['segment_id'], job.key, True, args.revision_approved)
            except (GuardError, Blocked) as exc:
                raise Blocked(str(exc))
            job.submit()
        if job.state['status']=='submission_uncertain':
            raise Blocked('Submission uncertain; recover exact conversation rather than sending again')
        deadline=time.monotonic()+900
        while job.state['status'] in ('submitted','pending') and time.monotonic()<deadline:
            job.poll()
            if job.state['status']=='pending': time.sleep(15)
        if job.state['status']=='video_available':
            job.download(Path.home()/'Downloads',args.output)
        if job.state['status']!='downloaded':
            raise Blocked('Job preserved in status '+job.state['status']+'; resume, never rerender blindly')
    print(json.dumps({'idea_id':args.idea,'status':'downloaded','artifact':job.state['artifact'],
                      'qc':'pending','record':str(job.path)},ensure_ascii=True))

if __name__=='__main__':
    try: main()
    except Blocked as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr); sys.exit(2)
    except Exception as exc:
        print('BLOCKED: '+type(exc).__name__+'; preserve local job state',file=sys.stderr); sys.exit(2)
