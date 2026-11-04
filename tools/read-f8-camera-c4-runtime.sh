#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
files=['/usr/libexec/f8-pro/camera-start.py','/etc/systemd/system/f8-camera-start.service',
 '/usr/local/lib/f8-pro/aiq-backend.py','/usr/local/lib/f8-pro/camera-preview.py',
 '/usr/local/lib/f8-pro/libf8-camera-pixels.so','/usr/local/bin/f8-camera-preview',
 '/usr/share/applications/f8-camera-preview.desktop','/home/f8test/Desktop/f8-camera-preview.desktop',
 '/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so','/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so',
 '/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json']
assets={}
front_iq=Path('/opt/f8-pro-camera/aiq-v6-c4/iqfiles-front-c4/gc5035_XHG-RKX11F-V5_HR232H65.json')
if front_iq.exists():files.extend([str(front_iq),str(front_iq.parent/'development-profile-manifest.json')])
for name in ['/usr/local/bin/f8-kamoso','/usr/local/lib/f8-pro/libf8-camera-relay-view.so',
 '/etc/modules-load.d/f8-camera-relay.conf','/etc/modprobe.d/f8-camera-relay.conf',
 '/usr/local/bin/f8-chromium-camera','/usr/local/share/f8-pro/camera-browser-test.html',
 '/usr/share/applications/f8-chromium-camera.desktop']:
 if Path(name).exists():files.append(name)
for name in files:
 p=Path(name);s=p.stat();assets[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':s.st_size,
 'mode':oct(s.st_mode&0o7777),'uid':s.st_uid,'gid':s.st_gid}
log=subprocess.check_output(['dmesg'],text=True)
health=subprocess.run(['systemctl','--failed','--no-pager'],capture_output=True,text=True)
state=Path('/run/user/1601/f8-camera-preview-status.json')
iq=json.loads(Path('/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json').read_text());scene=iq['main_scene'][0]['sub_scene'][0]['scene_isp30']
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'assets':assets,'failed_units':health.stdout,'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),
 'kernel_oops_found':any(s in log for s in ['Internal error:','Kernel panic','Oops:']),
 'preview_state':json.loads(state.read_text()) if state.exists() else None,
 'iq_policy':{'fps':scene['ae_calib']['CommCtrl']['AecFrameRateMode'],'wb':scene['wb_v21']['control']},
 'kernel_log_tail':log.splitlines()[-45:]},indent=2))
PY
