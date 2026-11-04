"""Upgrade only the known F1 files, preserving a complete rollback copy."""
import ast,base64,hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1];src=P/'armbian/camera';out=P/'outputs/armbian/f8-flash-f2'
report=json.loads((out/'module-check.json').read_text());module=(out/'f8-flash.ko').read_bytes()
assert report['all_import_crcs_verified'] and hashlib.sha256(module).hexdigest()==report['module_sha256']
old=json.loads((P/'outputs/armbian/f8-flash-f1/installation-manifest.json').read_text())
files={
 '/usr/libexec/f8-pro/flash-control.py':((src/'flash-control-f2.py').read_bytes(),0o755),
 '/usr/libexec/f8-pro/flash-panel.py':((src/'flash-panel-f2.py').read_bytes(),0o755),
 '/usr/share/polkit-1/actions/org.f8pro.flash.policy':((src/'org.f8pro.flash.policy').read_bytes(),0o644),
 '/usr/share/applications/f8-flash.desktop':((src/'f8-flash.desktop').read_bytes().replace(b'Comment=Test the rear flash with an automatic 0.5 second timeout',b'Comment=Rear flash brightness, steady light and blinking'),0o644),
 '/etc/modules-load.d/f8-flash.conf':(b'f8-flash\n',0o644),
 '/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-flash.ko':(module,0o644)}
for name,(data,mode) in files.items():
 if name.endswith('.py'):ast.parse(data)
 dest=P/'armbian/rootfs-overlay'/name.lstrip('/');assert dest.is_file()
 assert hashlib.sha256(dest.read_bytes()).hexdigest() in [old[name]['sha256'],hashlib.sha256(data).hexdigest()],name
 dest.write_bytes(data)
# Check the privileged protocol validator without executing privileged main().
tree=ast.parse((src/'flash-control-f2.py').read_text());ns={'re':re}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='command'],type_ignores=[]),'validator','exec'),ns)
for value in ['off','keepalive','steady 25','pulse 100','blink 25 100 5000']:assert ns['command'](value)==value
for value in ['steady 0','steady 101','blink 25 0 500','blink 25 500 5001','off extra','../../tmp','steady -1','steady 10; echo x']:
 try:ns['command'](value)
 except ValueError:pass
 else:raise AssertionError('Validator accepted '+value)
payload={n:{'data':base64.b64encode(d).decode(),'mode':m,'sha256':hashlib.sha256(d).hexdigest(),'old_sha256':old[n]['sha256']} for n,(d,m) in files.items()}
code='''import base64,hashlib,json,os,pwd,shutil,signal,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
root=Path('/sys/devices/platform/f8-flash');control=root/'control'
control.write_text('off\\n');assert 'mode=off ' in (root/'state').read_text()
files=PAYLOAD
for name,v in files.items():
 p=Path(name);assert p.is_file() and not p.is_symlink()
 assert hashlib.sha256(p.read_bytes()).hexdigest() in [v['old_sha256'],v['sha256']],'Conflicting file '+name
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
subprocess.run(u+['systemctl','--user','stop','f8-flash-panel'],capture_output=True,timeout=10)
for p in Path('/proc').glob('[0-9]*'):
 try:
  args=(p/'cmdline').read_bytes().split(b'\\0')
  if p.stat().st_uid==uid and b'/usr/libexec/f8-pro/flash-panel.py' in args:os.kill(int(p.name),signal.SIGTERM)
 except (FileNotFoundError,ProcessLookupError):pass
backup=Path('/var/lib/f8-pro/backups/flash-f1')
for name,v in files.items():
 p=Path(name);b=backup/name.lstrip('/');b.parent.mkdir(parents=True,exist_ok=True)
 if hashlib.sha256(p.read_bytes()).hexdigest()==v['old_sha256']:
  if b.exists():assert b.read_bytes()==p.read_bytes()
  else:shutil.copy2(p,b)
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256']
 p.write_bytes(data);p.chmod(v['mode']);os.chown(p,0,0)
subprocess.run(['depmod','-a',os.uname().release],check=True,timeout=20)
subprocess.run(['rmmod','f8_flash'],check=True,timeout=10)
subprocess.run(['modprobe','f8-flash'],check=True,timeout=10)
assert 'mode=off ' in (root/'state').read_text()
helper='/usr/libexec/f8-pro/flash-control.py'
p=subprocess.Popen([helper,'--session'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert p.stdout.readline().strip()=='ready'
try:
 p.stdin.write('steady 20\\n');p.stdin.flush();assert p.stdout.readline().strip()=='ok'
 assert 'mode=steady ' in (root/'state').read_text()
 second=subprocess.run([helper,'--session'],input='off\\n',capture_output=True,text=True,timeout=5)
 assert second.returncode!=0 and 'Another flash session' in second.stderr
 assert 'mode=steady ' in (root/'state').read_text()
finally:
 p.stdin.close();p.wait(timeout=5)
assert p.returncode==0 and 'mode=off ' in (root/'state').read_text()
r=subprocess.run(u+['systemctl','--user','show-environment'],capture_output=True,text=True,timeout=8);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-flash-panel',*['--setenv='+l for l in env],'--setenv=QT_QPA_PLATFORM=wayland','/usr/bin/python3','/usr/libexec/f8-pro/flash-panel.py'],capture_output=True,text=True,timeout=10)
print(json.dumps({'files':{n:v['sha256'] for n,v in files.items()},'panel_launch_exit':r.returncode,'panel_launch_message':r.stderr,'helper_eof_turns_off':True,'exclusive_session_verified':True,'autoload_configured':True,'cold_boot_verified':False,'final_state':(root/'state').read_text().strip(),'backup':str(backup),'boot_changed':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
compile(code,'f2-install','exec');(P/'local/hardware/flash-f2-install-runner.py').write_text(code)
(out/'installation-manifest.json').write_text(json.dumps({n:{k:v[k] for k in ['sha256','old_sha256','mode']} for n,v in payload.items()},indent=2)+'\n')
print('F2 payload ready; protocol validation passed')
