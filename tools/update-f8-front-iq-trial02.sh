#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json
from pathlib import Path
stage=Path('/home/f8test/.cache/f8-kamoso');folder=Path('/opt/f8-pro-camera/aiq-v6-c4/iqfiles-front-c4');name='gc5035_XHG-RKX11F-V5_HR232H65.json'
p=folder/name;assert hashlib.sha256(p.read_bytes()).hexdigest()=='5ff8756294c369de7f107332f18c3c7f37408604297201800da145f5e54e41ea'
data=(stage/name).read_bytes();assert hashlib.sha256(data).hexdigest()=='94133d191ed54a65130082110ea6b45c887ddfcefb36583cc0b7d43cf980efb6'
p.write_bytes(data);(folder/'development-profile-manifest.json').write_bytes((stage/'manifest.json').read_bytes())
print(json.dumps({'sha256':hashlib.sha256(data).hexdigest(),'lsc_geometry_converted':True}))
PY
