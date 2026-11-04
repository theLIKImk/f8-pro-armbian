"""Create an independent official-root copy for the first full desktop test."""
import hashlib
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
source=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
work=Path('/var/tmp/f8-pro-armbian/desktop-t1');work.mkdir(exist_ok=True)
root=work/'rootfs';root.mkdir(exist_ok=True)
out=P/'outputs/armbian/official-f8-desktop-t1';out.mkdir(exist_ok=True)
assert source!=root and root.parent==work
assert 'VERSION=26.8.1' in (source/'etc/armbian-release').read_text()
assert hashlib.sha256((source/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
marker=work/'copy-complete.json'
if not marker.exists():
    print('Copying independent official root, original root unchanged',flush=True)
    subprocess.run(['cp','-a','--reflink=auto',str(source)+'/.',str(root)+'/'],check=True)
    marker.write_text(json.dumps({'source':str(source),'root':str(root),'independent_copy':True},indent=2)+'\n')
assert (source/'etc/passwd').stat().st_ino!=(root/'etc/passwd').stat().st_ino
queries=['plasma-keyboard','maliit-keyboard','qt6-virtualkeyboard-plugin','qml6-module-qtquick-virtualkeyboard']
inventory=subprocess.run(['chroot',str(root),'dpkg-query','-W',*queries],capture_output=True,text=True)
(out/'keyboard-inventory.txt').write_text(inventory.stdout+inventory.stderr)
print(json.dumps({'desktop_root':str(root),'official_source_preserved':True,'keyboard_inventory':inventory.stdout}))
