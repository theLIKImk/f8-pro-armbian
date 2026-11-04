#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
out={}
for name in ['/usr/share/applications/f8-camera-preview.desktop','/home/f8test/Desktop/f8-camera-preview.desktop']:
 p=Path(name);s=p.read_text();assert 'Exec=/usr/local/bin/f8-camera-preview\n' in s
 assert 'Name=F8 Camera Preview\n' in s and 'Name[zh_CN]=F8 相机预览\n' in s
 s=s.replace('Name=F8 Camera Preview\n','Name=F8 Camera\n').replace('Name[zh_CN]=F8 相机预览\n','Name[zh_CN]=F8 相机（拍照录像）\n')
 p.write_text(s);out[name]=hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['desktop-file-validate','/usr/share/applications/f8-camera-preview.desktop'],check=True,timeout=8)
print(json.dumps(out,indent=2))
PY
