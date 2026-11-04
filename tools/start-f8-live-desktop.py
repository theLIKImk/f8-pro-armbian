"""Start the actual desktop on current r6, changing only RAM overlay files."""
import base64
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
out=P/'local/hardware/armbian-desktop-t1-live-20261030-01';out.mkdir(exist_ok=True)
runner=out/'start-desktop-runner.sh';resultfile=out/'start-result.json'
assert not runner.exists() and not resultfile.exists()
assert (P/'outputs/armbian/official-f8-desktop-t1/desktop-validation.json').exists()
debs={}
for prefix in ['plasma-keyboard_6.6.4','qml6-module-org-kde-layershell_6.6.4','qt6-virtualkeyboard-plugin_6.10.2']:
    matches=list((root/'var/cache/apt/archives').glob(prefix+'*.deb'));assert len(matches)==1,(prefix,matches)
    debs[matches[0].name]=base64.b64encode(matches[0].read_bytes()).decode()
files={}
paths=['etc/sddm.conf.d/90-f8-wayland.conf','etc/xdg/autostart/f8-desktop-session-record.desktop',
 'usr/libexec/f8-pro/desktop-session-record.sh','usr/libexec/f8-pro/desktop-status.py']
for name in paths:files['/'+name]=base64.b64encode((root/name).read_bytes()).decode()
for relative in ['.config/kwinrc','.config/kscreenlockerrc','.config/user-dirs.dirs',
 'Desktop/F8-Test-Status.desktop','Desktop/F8-Keyboard.desktop','Desktop/F8-Network.desktop']:
    files['/home/f8test/'+relative]=base64.b64encode((root/'etc/skel'/relative).read_bytes()).decode()
code='''import base64,datetime,json,os,pwd,subprocess,time
from pathlib import Path
assert any(s.split()[1:3]==['/','overlay'] for s in Path('/proc/mounts').read_text().splitlines())
stage=Path('/run/f8/desktop-live-t1');stage.mkdir()
backup=stage/'backup';backup.mkdir()
def cmd(args,timeout=60,check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError('Command failed: '+args[0]+' '+r.stderr[-1200:])
    return r
names=['sddm','kwin-wayland','plasma-workspace','libegl-mesa0','libgbm1','libgl1-mesa-dri']
before=cmd(['dpkg-query','-W',*names]).stdout
debfiles=[]
for name,encoded in DEBS.items():
    path=stage/name
    with path.open('xb') as stream:stream.write(base64.b64decode(encoded))
    debfiles.append(str(path))
install=cmd(['dpkg','-i',*debfiles],timeout=120)
(stage/'package-install.log').write_text(install.stdout+install.stderr)
assert cmd(['dpkg-query','-W',*names]).stdout==before,'Critical packages changed'
def preserve(path):
    dest=backup/path.relative_to('/');dest.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink():dest.with_suffix(dest.suffix+'.link').write_text(os.readlink(path))
    elif path.is_file():dest.write_bytes(path.read_bytes())
for path in [Path('/etc/sddm.conf'),*Path('/etc/sddm.conf.d').glob('*.conf')]:
    if path.exists() or path.is_symlink():preserve(path);path.unlink()
for name,encoded in FILES.items():
    path=Path(name);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() or path.is_symlink():preserve(path)
    if path.is_symlink():path.unlink()
    path.write_bytes(base64.b64decode(encoded))
    path.chmod(0o755 if name.endswith(('.sh','.desktop')) else 0o644)
    if name.startswith('/home/f8test/'):
        user=pwd.getpwnam('f8test');os.chown(path,user.pw_uid,user.pw_gid)
        for parent in path.parents:
            if str(parent)=='/home/f8test':break
            os.chown(parent,user.pw_uid,user.pw_gid)
if cmd(['getent','group','nopasswdlogin'],check=False).returncode:cmd(['groupadd','-r','nopasswdlogin'])
cmd(['usermod','-a','-G','video,render,nopasswdlogin','f8test'])
dm=Path('/etc/X11/default-display-manager');preserve(dm);dm.write_text('/usr/bin/sddm\\n')
mask=Path('/etc/systemd/system/sddm.service');preserve(mask)
if mask.is_symlink() and os.readlink(mask)=='/dev/null':mask.unlink()
drop=Path('/etc/systemd/system/sddm.service.d');drop.mkdir(exist_ok=True)
(drop/'95-f8-live-test.conf').write_text('[Unit]\\nRequires=f8-live-prepare.service\\nWants=systemd-user-sessions.service systemd-logind.service\\nAfter=f8-live-prepare.service systemd-user-sessions.service systemd-logind.service\\n[Service]\\nRestartSec=5\\n')
for name in ['sleep.target','suspend.target','hibernate.target','hybrid-sleep.target','suspend-then-hibernate.target']:
    path=Path('/etc/systemd/system')/name
    if path.exists() or path.is_symlink():preserve(path);path.unlink()
    path.symlink_to('/dev/null')
cmd(['systemctl','daemon-reload'])
cmd(['systemctl','stop','f8-live-status.service'])
try:cmd(['systemctl','start','sddm.service'],timeout=20)
except Exception:
    cmd(['systemctl','start','f8-live-status.service'],check=False);raise
marker=Path('/run/user/1601/f8-desktop/session.json')
for attempt in range(20):
    if marker.exists():break
    time.sleep(2)
states=cmd(['systemctl','show','sddm','f8-live-ssh','f8-live-power','-p','Id','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus']).stdout
logs=cmd(['journalctl','-b','-u','sddm','--no-pager','-n','160']).stdout
print(json.dumps({'scope':'Actual SDDM/Plasma Wayland startup on r6 RAM overlay',
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'critical_packages_unchanged':True,'session_marker_found':marker.exists(),
 'session':json.loads(marker.read_text()) if marker.exists() else None,
 'service_states':states,'sddm_journal':logs,'backup':str(backup)},indent=2))
'''.replace('DEBS',repr(debs)).replace('FILES',repr(files))
runner.write_text("set -eu\ntest \"$(uname -r)\" = 6.1.115-vendor-rk35xx\npython3 -I - <<'F8_DESKTOP_LIVE'\n"+code+'\nF8_DESKTOP_LIVE\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227','--script',str(runner),'--sudo','--timeout','240'],capture_output=True,text=True,timeout=260)
assert r.returncode==0,r.stderr[-2200:]
data=json.loads(r.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
with resultfile.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
