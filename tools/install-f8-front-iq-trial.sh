#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\0'
stage=Path('/home/f8test/.cache/f8-kamoso');name='gc5035_XHG-RKX11F-V5_HR232H65.json'
data=(stage/name).read_bytes();assert hashlib.sha256(data).hexdigest()=='5ff8756294c369de7f107332f18c3c7f37408604297201800da145f5e54e41ea'
folder=Path('/opt/f8-pro-camera/aiq-v6-c4/iqfiles-front-c4');assert not folder.exists();folder.mkdir(mode=0o755)
(folder/name).write_bytes(data);(folder/name).chmod(0o644)
(folder/'development-profile-manifest.json').write_bytes((stage/'manifest.json').read_bytes())
print(json.dumps({'path':str(folder),'profile_sha256':hashlib.sha256(data).hexdigest(),'autostart':False}))
PY
