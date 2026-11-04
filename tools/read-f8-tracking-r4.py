import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
W=Path('/var/lib/f8-pro/touch-diagnostic/r4')
out={'summary':json.loads((W/'summary.json').read_text())}
for name,p in [('kernel_frames',W/'frames.jsonl'),('application_events',Path('/home/likimk/.cache/f8-multitouch-test/trace-r4.jsonl'))]:
 out[name]=[json.loads(l) for l in p.read_text().splitlines() if l] if p.exists() else []
out['algorithm_input']=(W/'algorithm-input.txt').read_text() if (W/'algorithm-input.txt').exists() else None
out['probe_profile']=(W/'probe-profile.txt').read_text() if (W/'probe-profile.txt').exists() else None
out['probe_definitions_remaining']=[l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8touch_r4/' in l]
out['unit']=subprocess.run(['systemctl','show','f8-touch-capture-r4.service','-p','ActiveState','-p','Result'],capture_output=True,text=True,timeout=8).stdout
print(json.dumps(out))
