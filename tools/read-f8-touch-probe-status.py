import json,subprocess
from pathlib import Path
r=subprocess.run(['journalctl','-b','-u','f8-touch-capture-r3','--no-pager','-n','35'],capture_output=True,text=True,timeout=8)
print(json.dumps({'log':r.stdout,'probe_definitions':[l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8touch_r3' in l],'errors':Path('/sys/kernel/tracing/error_log').read_text() if Path('/sys/kernel/tracing/error_log').exists() else None}))
