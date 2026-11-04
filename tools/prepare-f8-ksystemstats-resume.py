import base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files={p.name:base64.b64encode(p.read_bytes()).decode() for p in (P/'armbian/kde/ksystemstats').iterdir() if p.is_file()}
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
w=Path('/var/tmp/f8-pro-ksystemstats-k1');assert w.exists()
subprocess.run(['systemctl','stop','f8-ksystemstats-build.service'],check=True,capture_output=True,timeout=15)
for name,data in json.loads(base64.b64decode(DATA)).items():assert '/' not in name;(w/name).write_bytes(base64.b64decode(data))
subprocess.run(['systemctl','restart','f8-ksystemstats-build.service'],check=True,capture_output=True,timeout=10)
print(json.dumps({'resumed':True}))
'''.replace('DATA',repr(base64.b64encode(json.dumps(files).encode()).decode()))
(P/'local/hardware/ksystemstats-build-resume-runner.py').write_text(code)
