"""Install guarded C4 blanking persistence, no restart of the camera service."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=(P/'armbian/camera/camera-start.py').read_bytes().replace(b'\r\n',b'\n')
compile(data,'camera-start.py','exec')
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\\0'
p=Path('/usr/libexec/f8-pro/camera-start.py');old=p.read_bytes()
assert hashlib.sha256(old).hexdigest()=='5a164f1b13fe3838b7c293ad8f57634c448a0bd009d35000a938e2785ec6fd25'
data=base64.b64decode(DATA);compile(data,str(p),'exec')
backup=Path('/var/lib/f8-pro/backups/camera-start-before-c4.py');assert not backup.exists()
backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(old);backup.chmod(0o644)
temp=p.with_name('camera-start.py.c4-new');assert not temp.exists()
temp.write_bytes(data);temp.chmod(0o755);temp.replace(p)
removed=[]
for name in ['gc5035_XHG-RKX11F-V5_HR232H65.json','ov8858_HS5885-BNSM1018-V01_default.json']:
 link=Path('/etc/iqfiles')/name
 assert link.is_symlink() and str(link.readlink())=='/opt/f8-pro-camera/aiq-v6-c4/iqfiles/'+name
 link.unlink();removed.append(str(link))
print(json.dumps({'installed_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'backup':str(backup),
 'global_trial_iq_symlinks_removed':removed,'private_iq_preserved':True,'service_restarted':False},indent=2))
'''.replace('DATA',repr(base64.b64encode(data).decode()))
runner=P/'local/hardware/camera-c4-root-update-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+"\nPY\n")
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=95)
assert r.returncode==0,r.stderr
result=json.loads(r.stdout)
(P/'local/hardware/camera-c4-root-update01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
