"""Install this verified build in the user's Applications folder and launch once."""
import hashlib,json,os,pwd,shutil,struct,subprocess,tarfile,time
from pathlib import Path,PurePosixPath
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
user=pwd.getpwnam('likimk');home=Path(user.pw_dir)
archive=home/'Phira-linux-arm64-v0.8.2-7505793.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='6f710fd40224eb926dbfdbb66894335082b8f4d18980422abc939ebbd0bed240'
apps=home/'Applications';assert not apps.is_symlink();apps.mkdir(exist_ok=True);os.chown(apps,user.pw_uid,user.pw_gid)
app=apps/'Phira-linux-arm64-v0.8.2';assert not app.is_symlink()
if not app.exists():
 with tarfile.open(archive) as t:
  for m in t.getmembers():
   p=PurePosixPath(m.name)
   assert p.parts and p.parts[0]==app.name and not p.is_absolute() and '..' not in p.parts
   assert m.isfile() or m.isdir(),'Only ordinary application files allowed'
   assert m.size<128*1024*1024
  t.extractall(apps,filter='data')
 for p in [app,*app.rglob('*')]:assert not p.is_symlink();os.chown(p,user.pw_uid,user.pw_gid)
binary=app/'phira';assert hashlib.sha256(binary.read_bytes()).hexdigest()=='93b075b5cd8db9b8c1657677a83faae0adc62e1ee42c3d5b6c1a348e2f4c2ae8'
assert struct.unpack_from('<H',binary.read_bytes(),18)[0]==183
base=['runuser','-u',user.pw_name,'--','env','XDG_RUNTIME_DIR=/run/user/'+str(user.pw_uid),'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/'+str(user.pw_uid)+'/bus']
def run(a,timeout=12):return subprocess.run(a,capture_output=True,text=True,timeout=timeout)
out={'installed':str(app),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'architecture':'AArch64','boot_changed':False}
r=run(base+['ldd',str(binary)]);out['ldd']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};assert r.returncode==0 and 'not found' not in r.stdout,out['ldd']
r=run(base+['/usr/bin/python3',str(app/'install-desktop.py')]);out['menu']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};assert r.returncode==0,out['menu']
entry=home/'.local/share/applications/f8-phira-arm64.desktop';assert entry.read_text().startswith('[Desktop Entry]\n')
r=run(base+['systemctl','--user','show-environment']);assert r.returncode==0,r.stderr
whitelist=['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS']
env={k:v for l in r.stdout.splitlines() if '=' in l for k,v in [l.split('=',1)] if k in whitelist}
if not env.get('DISPLAY') or not env.get('XAUTHORITY'):
 for p in Path('/proc').glob('[0-9]*'):
  try:
   if p.stat().st_uid==user.pw_uid and (p/'comm').read_text().strip()=='plasmashell':
    selected={k.decode():v.decode() for x in (p/'environ').read_bytes().split(b'\0') if b'=' in x for k,v in [x.split(b'=',1)] if k.decode() in whitelist};env.update(selected);break
  except (OSError,UnicodeError):pass
assert env.get('DISPLAY'),'No XWayland display in the active desktop session'
out['display_environment']=env
launch=['systemd-run','--user','--collect','--unit=f8-phira-arm64','--property=WorkingDirectory='+str(app),'--setenv=RUST_LOG=info',*['--setenv='+k+'='+v for k,v in env.items()],str(app/'run-phira.sh')]
r=run(base+launch);out['launch']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
time.sleep(12)
r=run(base+['systemctl','--user','show','f8-phira-arm64','-p','ActiveState','-p','SubState','-p','Result','-p','MainPID','-p','ExecMainStatus']);out['service']=r.stdout
r=run(base+['journalctl','--user','-b','-u','f8-phira-arm64','--no-pager','-n','40']);out['startup_log']=r.stdout
if shutil.which('xwininfo'):
 r=run(base+['env',*['%s=%s'%(k,v) for k,v in env.items()],'xwininfo','-name','Phira']);out['window']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
main=next((int(l.split('=',1)[1]) for l in out['service'].splitlines() if l.startswith('MainPID=')),0)
if main and Path('/proc',str(main)).exists():
 out['process_exe']=str((Path('/proc')/str(main)/'exe').resolve())
 out['drm_fds']=[]
 for p in (Path('/proc')/str(main)/'fd').glob('*'):
  try:
   if str(p.resolve()).startswith('/dev/dri/'):
    info=(Path('/proc')/str(main)/'fdinfo'/p.name).read_text();out['drm_fds'].append({'device':str(p.resolve()),'drm_info':[l for l in info.splitlines() if l.startswith('drm-')]})
  except OSError:pass
out['startup_process_alive']='ActiveState=active' in out['service'] and main>0
print(json.dumps(out,indent=2))
