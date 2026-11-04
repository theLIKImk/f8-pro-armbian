"""Keep the WSL build session alive and report only phase changes."""
import json,time
from pathlib import Path
W=Path('/var/tmp/f8-pro-phira-arm64');pid=int((W/'build.pid').read_text());previous=None
while True:
 p=Path('/proc')/str(pid)/'cmdline'
 alive=p.exists() and b'build-phira-arm64.py' in p.read_bytes()
 try:
  data=json.loads((W/'status.json').read_text());state={k:v.get('stage') for k,v in data.items()}
 except (OSError,ValueError):state={}
 if state!=previous:print(json.dumps({'alive':alive,'stages':state}),flush=True);previous=state
 if not alive:
  print(json.dumps({'finished':True,'stages':state}),flush=True);break
 time.sleep(5)
