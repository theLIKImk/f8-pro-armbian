"""Summarize time-aligned kernel and Qt touch traces, without declaring acceptance."""
import argparse,collections,json,math,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path);a=p.parse_args()
outer=json.loads(a.input.read_text(encoding='utf-8-sig'));data=json.loads(outer['stdout'])
start=data['summary'].get('start_monotonic')
assert start is not None,'User has not started the diagnostic'
phases=[(0,5,'prepare'),(5,13,'single'),(13,16,'lift1'),(16,25,'two'),(25,28,'lift2'),(28,45,'sequential_five'),(45,48,'lift3'),(48,60,'simultaneous_five'),(60,65,'finish')]
out={'summary':data['summary'],'unit':data['unit'],'phases':{}}
for lo,hi,name in phases:
 frames=[f for f in data['kernel_frames'] if f['kind']=='frame' and lo<=f['t']-start<hi]
 events=[e for e in data['application_events'] if lo<=e['t']-start<hi]
 durations=collections.Counter();transitions=[];jumps=[];prev=None
 for f in frames:
  if prev:
   dt=f['t']-prev['t'];durations[len(prev['points'])]+=max(0,dt)
   old={p['slot']:p for p in prev['points']};new={p['slot']:p for p in f['points']}
   for ident in old.keys()&new.keys():
    x,y=old[ident],new[ident]
    if all(k in x and k in y for k in ['x','y']):
     dist=math.hypot(y['x']-x['x'],y['y']-x['y'])
     if dist>70 and dt<.1:jumps.append({'elapsed':round(f['t']-start,3),'slot':ident,'distance':round(dist,1),'dt':round(dt,4),'from':x,'to':y})
  if f['changes']:transitions.append({'elapsed':round(f['t']-start,3),'count':len(f['points']),'changes':f['changes']})
  prev=f
 times=[b['t']-a['t'] for a,b in zip(frames,frames[1:])]
 out['phases'][name]={'frames':len(frames),'kernel_peak':max([len(f['points']) for f in frames],default=0),'contact_count_seconds_between_frames':{str(k):round(v,3) for k,v in sorted(durations.items())},'frame_interval_median_ms':round(statistics.median(times)*1000,2) if times else None,'frame_interval_max_ms':round(max(times)*1000,2) if times else None,'transitions':transitions,'jump_count':len(jumps),'jumps_first20':jumps[:20],'qt_events':len(events),'qt_cancel_count':sum(e['event']=='TouchCancel' for e in events),'qt_peak':max([sum(p['state']!='Released' for p in e['points']) for e in events],default=0)}
dest=a.input.with_name(a.input.stem+'-analysis.json');dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
