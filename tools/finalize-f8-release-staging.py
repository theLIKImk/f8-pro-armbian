from pathlib import Path
import hashlib,json,os,re,subprocess
P=Path(__file__).resolve().parents[1];B=Path('/var/tmp/f8-pro-armbian/release-r1');R=B/'rootfs'
assert (B/'first-run-native-test.json').exists()
assert R.resolve()==Path('/var/tmp/f8-pro-armbian/release-r1/rootfs')
for name in ['ssh.service','ssh.socket','sshd.service']:
 f=R/'etc/systemd/system'/name
 if f.is_symlink() and os.readlink(f)=='/dev/null':f.unlink()
sshd=R/'etc/ssh/sshd_config';sshd.write_text(re.sub(r'^PermitRootLogin\s+\S+','PermitRootLogin no',sshd.read_text(),flags=re.M))
drop=R/'etc/ssh/sshd_config.d/00-f8-local-account.conf';drop.write_text('PermitRootLogin no\nPasswordAuthentication yes\nKbdInteractiveAuthentication no\n')
# Do not replace the Chinese OSK installed during release configuration.
assert (R/'usr/share/f8-pro/fcitx5/manifest.json').is_file(),'Fcitx5 runtime missing from release root'
kwin=(P/'armbian/fcitx5/kwinrc').read_text()
for name in ['etc/skel/.config/kwinrc','home/f8setup/.config/kwinrc']:(R/name).write_text(kwin)
subprocess.run(['chroot',str(R),'/usr/sbin/visudo','-cf','/etc/sudoers'],check=True)
assert not list((R/'etc/ssh').glob('ssh_host_*'))
assert not (R/'var/lib/f8-pro/first-run/complete.json').exists()
assert not (R/'home/f8qatest').exists() and not (R/'home/f8qadiag').exists()
assert (R/'usr/lib/systemd/system/ssh.service').exists()
assert hashlib.sha256((R/'usr/libexec/f8-pro/desktop-hardware.sh').read_bytes()).hexdigest()=='666a21a21f962dbde68f10c8978c16c44ce4a30873f118845a1b70eb30b4f912'
record=json.loads((B/'configured.json').read_text())
source=P/'armbian/first-run/first-run-apply.py';installed=R/'usr/local/lib/f8-pro/first-run-apply.py'
assert source.read_bytes()==installed.read_bytes()
record['critical_files']['/usr/local/lib/f8-pro/first-run-apply.py']=hashlib.sha256(installed.read_bytes()).hexdigest()
for name in ['/usr/libexec/f8-pro/desktop-hardware.sh','/usr/libexec/f8-pro/f8_otg_vbus_u2.ko','/etc/systemd/system/sddm.service.d/96-f8-status-handoff.conf','/etc/ssh/sshd_config.d/00-f8-local-account.conf','/etc/skel/.config/kwinrc']:
 record['critical_files'][name]=hashlib.sha256((R/name.lstrip('/')).read_bytes()).hexdigest()
record['first_run_native_test_passed']=True
(B/'configured.json').write_text(json.dumps(record,indent=2)+'\n')
print('Staging finalized; all sudoers parsed, SSH opt-in, known C4 boot guards matched')
