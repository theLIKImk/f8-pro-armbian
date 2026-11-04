import base64,io,json,tarfile,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parents[1];A=P/'armbian/kde/ksystemstats'
V=P/'vendor/kde-ksystemstats-6.6.6';V.mkdir(exist_ok=True)
tar=V/'source.tar.gz'
if not tar.exists():tar.write_bytes(urllib.request.urlopen('https://codeload.github.com/KDE/ksystemstats/tar.gz/refs/tags/v6.6.6',timeout=30).read())
files={'source.tar.gz':base64.b64encode(tar.read_bytes()).decode()}
for p in A.iterdir():
 if p.is_file():files[p.name]=base64.b64encode(p.read_bytes()).decode()
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
w=Path('/var/tmp/f8-pro-ksystemstats-k1');w.mkdir(mode=0o700,exist_ok=True)
assert not (w/'status.json').exists(),'Do not overwrite an existing build'
for name,value in json.loads(base64.b64decode(DATA)).items():
 assert '/' not in name;(w/name).write_bytes(base64.b64decode(value))
r=subprocess.run(['systemd-run','--unit=f8-ksystemstats-build','--property=RuntimeMaxSec=1200','/usr/bin/python3',str(w/'build-native.py')],capture_output=True,text=True,check=True,timeout=10)
print(json.dumps({'started':True,'work':str(w),'message':r.stderr}))
'''.replace('DATA',repr(base64.b64encode(json.dumps(files).encode()).decode()))
(P/'local/hardware/ksystemstats-build-start-runner.py').write_text(code)
