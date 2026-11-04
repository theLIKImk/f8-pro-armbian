"""Offline timing analysis of retained R3/R4/R5 traces; no device changes."""
import hashlib,json,re,statistics
from pathlib import Path
P=Path(__file__).resolve().parents[1];results=[]
for round_number in [3,4,5]:
 p=P/f'local/hardware/multitouch-r{round_number}-trace01.json'
 d=json.loads(json.loads(p.read_text())['stdout'])
 raw=[float(m[1]) for line in d['algorithm_input'].splitlines() if (m:=re.search(r'\s(\d+\.\d+):\s+raw:',line))]
 evdev=[f['t'] for f in d['kernel_frames'] if f.get('kind')=='frame']
 summary={'round':round_number,'source':str(p.relative_to(P)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 for name,times in [('algorithm_entry',raw),('evdev',evdev)]:
  intervals=[(b-a)*1000 for a,b in zip(times,times[1:]) if 0<b-a<.1]
  fast=[v for v in intervals if 13.5<v<17]
  summary[name]={'records':len(times),'intervals_under_100ms':len(intervals),'median_interval_ms':statistics.median(intervals),'fast_cluster_13_5_to_17ms_samples':len(fast),'fast_cluster_median_ms':statistics.median(fast),'fast_cluster_hz':1000/statistics.median(fast),'shortest_observed_interval_ms':min(intervals)}
 results.append(summary)
report={'analysis_date':'2026-11-03','source_capture_date':'2026-11-02','method':'Retained algorithm-entry and evdev timestamps; exclude gaps >=100ms; describe 13.5-17ms fast interval cluster separately from overall median. No claim of continuous sustainable maximum.','results':results,'conclusion':'Observed fast delivery cadence approximately 67Hz. Controller internal scanning frequency and exact hardware maximum remain unverified. IRQ scheduling, filtering, motion, missing contacts and application delivery can change observed event cadence.','device_modified':False}
dest=P/'local/hardware/multitouch-report-rate-analysis01.json';dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fast_algorithm_entry_hz':[round(r['algorithm_entry']['fast_cluster_hz'],2) for r in results],'evdev_median_ms':[round(r['evdev']['median_interval_ms'],3) for r in results],'hardware_maximum_verified':False},indent=2))
