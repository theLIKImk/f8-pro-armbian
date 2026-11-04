import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=P/'outputs/armbian/official-f8-desktop-t1r1/preflight.json'
m=json.loads(p.read_text())
original=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs/usr/libexec/f8-pro/desktop-hardware.sh')
assert hashlib.sha256(original.read_bytes()).hexdigest()==m['known_original_helper_sha256']
assert hashlib.sha256((P/'armbian/desktop-t1/desktop-hardware.sh').read_bytes()).hexdigest()==m['replacement_helper_sha256']
m['original_helper_source_verified']=True
p.write_text(json.dumps(m,indent=2)+'\n')
print('Original helper guard verified against frozen T1 root; replacement source verified')
