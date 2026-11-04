import base64
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=base64.b64encode((P/'armbian/official-graphics/touch-events.py').read_bytes()).decode()
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/var/lib/f8-pro/touch-diagnostic');p.mkdir(parents=True,exist_ok=True);p.chmod(0o700)
script=p/'capture.py';script.write_bytes(base64.b64decode(DATA));script.chmod(0o700)
r=subprocess.run(['systemd-run','--collect','--unit=f8-touch-capture-r1','--property=RuntimeMaxSec=95','/usr/bin/python3',str(script),'--seconds','80','--discovery-seconds','0','--output',str(p/'capture-r1.json')],capture_output=True,text=True,timeout=8)
print(json.dumps({'exit':r.returncode,'message':r.stderr}))
'''.replace('DATA',repr(data));(P/'local/hardware/multitouch-capture-runner.py').write_text(code)
