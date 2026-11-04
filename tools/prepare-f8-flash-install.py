"""Stage the tested F1 module and panel; generate a credential-free SSH payload."""
import ast,base64,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
P=Path(__file__).resolve().parents[1];src=P/'armbian/camera';out=P/'outputs/armbian/f8-flash-f1'
report=json.loads((out/'module-check.json').read_text());module=(out/'f8-flash.ko').read_bytes()
assert report['all_import_crcs_verified'] and hashlib.sha256(module).hexdigest()==report['module_sha256']
files={
 '/usr/libexec/f8-pro/flash-control.py':((src/'flash-control.py').read_bytes(),0o755),
 '/usr/libexec/f8-pro/flash-panel.py':((src/'flash-panel.py').read_bytes(),0o755),
 '/usr/share/polkit-1/actions/org.f8pro.flash.policy':((src/'org.f8pro.flash.policy').read_bytes(),0o644),
 '/usr/share/applications/f8-flash.desktop':((src/'f8-flash.desktop').read_bytes(),0o644),
 '/etc/modules-load.d/f8-flash.conf':(b'f8-flash\n',0o644),
 '/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-flash.ko':(module,0o644)}
for name,(data,mode) in files.items():
 if name.endswith('.py'):ast.parse(data)
 if name.endswith('.policy'):ET.fromstring(data)
 dest=P/'armbian/rootfs-overlay'/name.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert dest.read_bytes()==data,'Preserve conflicting overlay '+name
 else:dest.write_bytes(data)
payload={n:{'data':base64.b64encode(d).decode(),'mode':m,'sha256':hashlib.sha256(d).hexdigest()} for n,(d,m) in files.items()}
code='''import base64,hashlib,json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
assert Path('/sys/module/f8_flash').exists()
led=Path('/sys/class/leds/f8:white:flash');assert (led/'brightness').read_text().strip()=='0'
files=PAYLOAD
for name,v in files.items():
 p=Path(name);assert not p.is_symlink()
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256']
 if p.exists():assert p.read_bytes()==data,'Conflicting file '+name
for name,v in files.items():
 p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(v['data']));p.chmod(v['mode']);os.chown(p,0,0)
subprocess.run(['depmod','-a',os.uname().release],check=True,timeout=20)
r=subprocess.run(['modprobe','--show-depends','f8-flash'],capture_output=True,text=True,timeout=8);assert r.returncode==0,r.stderr
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
r=subprocess.run(u+['systemctl','--user','show-environment'],capture_output=True,text=True,timeout=8);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-flash-panel',*['--setenv='+l for l in env],'--setenv=QT_QPA_PLATFORM=wayland','/usr/bin/python3','/usr/libexec/f8-pro/flash-panel.py'],capture_output=True,text=True,timeout=10)
print(json.dumps({'files':{n:v['sha256'] for n,v in files.items()},'panel_launch_exit':r.returncode,'panel_launch_message':r.stderr,'autoload_configured':True,'cold_boot_verified':False,'final_brightness':(led/'brightness').read_text().strip(),'boot_changed':False},indent=2))
'''.replace('PAYLOAD',repr(payload))
compile(code,'flash-install','exec');(P/'local/hardware/flash-f1-install-runner.py').write_text(code)
(out/'installation-manifest.json').write_text(json.dumps({n:{'sha256':v['sha256'],'mode':v['mode']} for n,v in payload.items()},indent=2)+'\n')
print('F1 install payload and rootfs overlay ready')
