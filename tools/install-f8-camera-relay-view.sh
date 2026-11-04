#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json
from pathlib import Path
data=Path('/home/f8test/.cache/f8-kamoso/f8-camera-relay-view.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='7f0b7a33c6cc32df8117e2665218ef6c0cfa0f79b2f779f753a91d406694764e'
p=Path('/usr/local/lib/f8-pro/libf8-camera-relay-view.so');assert not p.exists();p.write_bytes(data);p.chmod(0o644)
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'global_preload':False}))
PY
