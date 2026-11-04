from pathlib import Path
import base64
P=Path(__file__).resolve().parents[1]
items={}
for source,target,mode in [('setup-cleanup.py','/usr/local/lib/f8-pro/setup-cleanup.py',0o755),('f8-setup-cleanup.service','/etc/systemd/system/f8-setup-cleanup.service',0o644),('f8-setup-cleanup.timer','/etc/systemd/system/f8-setup-cleanup.timer',0o644)]:
 items[target]={'data':base64.b64encode((P/'armbian/first-run'/source).read_bytes()).decode(),'mode':mode}
code='''import base64,json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/etc/f8-pro-release-r1').is_file()
complete=json.loads(Path('/var/lib/f8-pro/first-run/complete.json').read_text())
assert complete['username']=='likimk'
for name,item in ITEMS.items():
 p=Path(name);data=base64.b64decode(item['data'])
 assert not p.is_symlink()
 if p.exists():assert p.read_bytes()==data,'Different existing cleanup asset: '+name
 else:p.write_bytes(data);p.chmod(item['mode'])
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
r=subprocess.run(['/usr/bin/python3','-I','/usr/local/lib/f8-pro/setup-cleanup.py','--apply'],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stdout+r.stderr
result=json.loads(r.stdout)
if result.get('action','').startswith('pending-'):
 subprocess.run(['systemctl','enable','--now','f8-setup-cleanup.timer'],check=True,timeout=15)
try:pwd.getpwnam('f8setup');exists=True
except KeyError:exists=False
print(json.dumps({'cleanup':result,'setup_account_exists':exists,'new_account':pwd.getpwnam('likimk').pw_name,'wifi_changes':False},indent=2))
'''.replace('ITEMS',repr(items))
(P/'local/hardware/setup-cleanup-install-runner.py').write_text(code)
print('Cleanup installer prepared without credentials')
