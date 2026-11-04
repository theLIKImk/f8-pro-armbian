"""Finalize native writable-root configuration without private credentials."""
import hashlib
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
out=P/'outputs/armbian/official-f8-desktop-t1'
assert (out/'desktop-validation.json').exists()
assert not (out/'native-root-preparation.json').exists()
live=json.loads((P/'local/hardware/armbian-desktop-t1-live-20261030-01/start-result.json').read_text())
assert live['session']['session_type']=='wayland'
for name in ['desktop-prepare.sh','native-prepare.sh']:
    path=root/'usr/libexec/f8-pro'/name
    path.write_bytes((P/'armbian/desktop-t1'/name).read_bytes());path.chmod(0o755)
public=Path('/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519.pub')
if public.exists():key=public.read_text().strip()
else:key=subprocess.check_output(['ssh-keygen','-y','-f',str(public.with_suffix(''))],text=True).strip()
assert key.startswith('ssh-ed25519 ') and len(key.split())>=2
dest=root/'usr/share/f8-pro/test-authorized-keys';dest.parent.mkdir(exist_ok=True)
dest.write_text(' '.join(key.split()[:2])+'\n');dest.chmod(0o644)
(root/'etc/f8-pro-native-desktop-t1').write_text('Official Armbian native writable F8 desktop T1\n')
(root/'etc/fstab').write_text('# Native root mounted by verified initramfs; no automatic extra partition mounts.\n')
(root/'etc/skel/.config/kwalletrc').write_text('[Wallet]\nEnabled=false\n')
(root/'usr/libexec/f8-pro/desktop-status.py').write_text((P/'armbian/desktop-t1/desktop-status.py').read_text().replace(
 'Desktop settings are temporary in this test edition. SSH remains available.',
 'Desktop settings are stored on the native root partition. SSH remains available.'))
logger=root/'usr/libexec/f8-pro/graphics-report'
text=logger.read_text();anchor='    cat /etc/armbian-release >"$disk/ARMBIAN.TXT" 2>&1\n'
text=text.replace(anchor,anchor+'''    [ ! -f /etc/ssh/ssh_host_ed25519_key.pub ] || cp /etc/ssh/ssh_host_ed25519_key.pub "$disk/SSHKEY.PUB"
    [ ! -f /etc/ssh/ssh_host_ed25519_key.pub ] || ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub >"$disk/HOSTKEY.TXT"
    cat /etc/f8-pro-native-desktop-t1 >"$disk/ROOTTYPE.TXT" 2>&1
''')
logger.write_text(text)
assert not list((root/'etc/ssh').glob('ssh_host_*_key'))
assert not list((root/'etc/NetworkManager/system-connections').glob('*'))
assert not (root/'home/f8test').exists()
record={'native_writable_root':True,'root_partition_start_sectors':491520,
 'boot_partition_start_sectors':32768,'contains_user_public_authorized_key':True,
 'public_key_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
 'contains_wifi_password':False,'contains_ssh_host_private_key':False,
 'host_identity_generated_on_first_boot':True,'first_boot_wifi_connection_from_desktop':True,
 'sddm_autologin_f8test':True,'user_desktop_touch_keyboard_confirmed':True,
 'native_root_cold_boot_tested':False}
(out/'native-root-preparation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
