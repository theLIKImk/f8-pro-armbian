import json,subprocess,os
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
out={}
for k,args in [('packages',['dpkg-query','-W','kwin*','libkwin*','qt6-base-dev','cmake','g++']),('libraries',['find','/usr/lib/aarch64-linux-gnu','-maxdepth','2','-iname','*kwin*']),('space',['df','-h','/','/var/tmp']),('services',['systemctl','status','sddm','--no-pager'])]:
 r=subprocess.run(args,capture_output=True,text=True,timeout=10);out[k]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
for p in Path('/usr/lib/aarch64-linux-gnu').glob('libkwin.so*'):
 r=subprocess.run(['nm','-D','-C',str(p)],capture_output=True,text=True,timeout=10);out[str(p)]=[x for x in r.stdout.splitlines() if 'GlobalShortcutFilter' in x or 'InputEventFilter' in x][:60]
print(json.dumps(out,indent=2))
