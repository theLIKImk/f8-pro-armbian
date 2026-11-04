"""Read-only rsync from the verified tablet into an isolated release tree."""
from pathlib import Path
import json,subprocess,time
P=Path(__file__).resolve().parents[1]
B=Path('/var/tmp/f8-pro-armbian/release-r1')
R=B/'rootfs'
B.mkdir(exist_ok=True)
assert B.resolve()==Path('/var/tmp/f8-pro-armbian/release-r1')
assert not (B/'snapshot-complete.json').exists()
ssh=['ssh','-T','-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=f8-desktop-t1','-o','UserKnownHostsFile=/var/tmp/f8-pro-armbian/desktop-t1-known-hosts','-o','ConnectTimeout=8']
import shlex
excludes=['/dev/***','/proc/***','/sys/***','/run/***','/tmp/***','/mnt/***','/media/***','/home/***','/root/***','/lost+found/***',
 '/etc/shadow*','/etc/gshadow*','/etc/ssh/ssh_host_*','/etc/NetworkManager/system-connections/***','/etc/netplan/***','/etc/ssl/private/***','/etc/credstore*/***','/etc/wireguard/***','/etc/sddm.f8-source/***',
 '/var/cache/***','/var/log/***','/var/log.hdd/***','/var/crash/***','/var/tmp/***','/var/backups/***','/var/spool/***','/var/mail/***',
 '/var/lib/NetworkManager/***','/var/lib/bluetooth/***','/var/lib/sddm/***','/var/lib/f8-pro/***','/var/lib/systemd/random-seed','/var/lib/systemd/credential.secret','/var/lib/AccountsService/users/***','/var/lib/AccountsService/icons/***',
 '/var/lib/dhcp/***','/var/lib/dhcpcd/***','/var/lib/chrony/***','/var/lib/private/***','/var/lib/sss/***','/var/lib/avahi-autoipd/***','/var/lib/colord/***','/var/lib/cups/***']
if not R.exists():
 R.mkdir()
 subprocess.run(['cp','-a','--reflink=auto','/var/tmp/f8-pro-armbian/desktop-t1/rootfs/.',str(R)],check=True)
args=['rsync','-aHAXx','--numeric-ids','--delete','--delete-excluded','--stats','--timeout=60','--rsync-path=sudo -n rsync','-e',shlex.join(ssh)]
args += ['--exclude='+x for x in excludes]
with (B/'snapshot.log').open('w') as log:
 subprocess.run(args+['f8test@192.168.1.227:/',str(R)+'/'],stdout=log,stderr=subprocess.STDOUT,check=True)
# Only board/session defaults, never an unrestricted home copy.
assets=['.config/kwinrc','.config/plasmakeyboardrc','.config/kscreenlockerrc','.config/f8-cover.json','.config/systemd/user/f8-cover-screen.service']
for name in assets:
 target=B/'user-defaults'/name;target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['rsync','-a','-e',shlex.join(ssh),'f8test@192.168.1.227:/home/f8test/'+name,str(target)],check=True)
(B/'snapshot-complete.json').write_text(json.dumps({'time':time.time(),'root':str(R),'excludes':excludes,'user_allowlist':assets,'source_is_live_file_copy':True,'target_device_writes':False},indent=2)+'\n')
print('Snapshot complete',flush=True)
