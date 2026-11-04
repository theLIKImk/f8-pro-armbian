"""Generated with the exact local build hash before remote execution."""
import hashlib,json,os,pwd,shutil,signal,struct,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
user=pwd.getpwnam('likimk');a=Path(user.pw_dir)/'Applications/Phira-linux-arm64-v0.8.2'
incoming=Path(user.pw_dir)/'phira-f8-r1.incoming';expected='__BINARY_SHA256__'
data=incoming.read_bytes();assert hashlib.sha256(data).hexdigest()==expected
assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183
assert a.is_dir() and not a.is_symlink() and not (a/'phira').is_symlink()
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{user.pw_uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user.pw_uid}/bus']
def run(args):return subprocess.run(args,capture_output=True,text=True,timeout=12)
r=run(u+['systemctl','--user','stop','f8-phira-arm64.service']);assert r.returncode==0 or 'not loaded' in r.stderr,r.stderr
for p in Path('/proc').glob('[0-9]*'):
 try:
  if p.stat().st_uid==user.pw_uid and (p/'exe').resolve()==a/'phira':
   os.kill(int(p.name),signal.SIGTERM)
   for _ in range(50):
    if not p.exists() or (p/'exe').resolve()!=a/'phira':break
    time.sleep(0.1)
   assert not p.exists() or (p/'exe').resolve()!=a/'phira','Game did not stop'
 except FileNotFoundError:pass
backup=a/'phira.upstream-7505793'
if not backup.exists():
 assert hashlib.sha256((a/'phira').read_bytes()).hexdigest()=='93b075b5cd8db9b8c1657677a83faae0adc62e1ee42c3d5b6c1a348e2f4c2ae8'
 shutil.copy2(a/'phira',backup);os.chown(backup,user.pw_uid,user.pw_gid)
current_hash=hashlib.sha256((a/'phira').read_bytes()).hexdigest()
previous=a/('phira.previous-'+current_hash[:12])
if current_hash!=expected and not previous.exists():
 shutil.copy2(a/'phira',previous);os.chown(previous,user.pw_uid,user.pw_gid)
temp=a/'phira.f8tmp';assert not temp.is_symlink();temp.write_bytes(data);temp.chmod(0o755);os.chown(temp,user.pw_uid,user.pw_gid);temp.replace(a/'phira')
r=run(u+['ldd',str(a/'phira')]);assert r.returncode==0 and 'not found' not in r.stdout,r.stdout
r=run(u+['systemctl','--user','show-environment']);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
r=run(u+['systemd-run','--user','--collect','--unit=f8-phira-arm64','--property=WorkingDirectory='+str(a),*['--setenv='+l for l in env],'--setenv=RUST_LOG=info','--setenv=PHIRA_TOUCH_DIAGNOSTICS=1',str(a/'run-phira.sh')]);assert r.returncode==0,r.stderr
time.sleep(10)
o={'binary_sha256':expected,'backup':str(backup),'data_preserved':True}
o['service']=run(u+['systemctl','--user','show','f8-phira-arm64','-p','ActiveState','-p','MainPID','-p','Result']).stdout
r=run(u+['pactl','--format=json','list','sink-inputs']);assert r.returncode==0
o['audio']=[{'sample_specification':v.get('sample_specification'),'mute':v.get('mute'),'sink':v.get('sink')} for v in json.loads(r.stdout) if 'phira' in json.dumps(v.get('properties',{})).lower()]
print(json.dumps(o,indent=2))
