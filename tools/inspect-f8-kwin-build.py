import json,subprocess,os
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
o={}
for k,a in [('source',['apt-cache','showsrc','kwin']),('policy',['apt-cache','policy','libkwin6','kwin-dev']),('sources',['find','/etc/apt/sources.list.d','-maxdepth','1','-type','f']),('buildpaths',['find','/var/tmp/f8-pro-ksystemstats-k1','-maxdepth','2','-type','d'])]:
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);o[k]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
print(json.dumps(o,indent=2))
