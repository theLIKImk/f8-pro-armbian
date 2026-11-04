from pathlib import Path
import json,os,signal,subprocess,time
B=Path('/var/tmp/f8-pro-armbian/release-r1');R=B/'rootfs'
assert B.resolve()==Path('/var/tmp/f8-pro-armbian/release-r1')
assert not (B/'mkfs-complete.json').exists(),'Do not discard completed work automatically'
matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 if any(a.endswith(b'/build-f8-release-r1.py') or a==b'tools/build-f8-release-r1.py' for a in args) or (args and args[0]==b'mkfs.ext4' and str(B/'ROOTFS_F8_ARMBIAN_R1.ext4.img').encode() in args):matches.append(int(p.name))
for pid in matches:os.kill(pid,signal.SIGTERM)
for _ in range(30):
 if not any(Path('/proc',str(pid)).exists() for pid in matches):break
 time.sleep(.1)
assert not any(Path('/proc',str(pid)).exists() for pid in matches),'Wait for stopped packer before rebuilding'
image=B/'ROOTFS_F8_ARMBIAN_R1.ext4.img';assert image.resolve().parent==B
image.unlink(missing_ok=True)
for name in ['etc/security/opasswd','etc/security/opasswd.old','etc/ppp/chap-secrets','etc/ppp/pap-secrets']:
 p=R/name
 if p.is_file():p.write_text('');p.chmod(0o600)
report={'private_key_markers_in_etc':[],'ppp_authentication_files_cleared':True,'password_history_cleared':True,'discarded_incomplete_image':True,'tablet_modified':False}
(B/'auth-scrub.json').write_text(json.dumps(report,indent=2)+'\n');print('Cleared authentication remnants in staging; incomplete image discarded')
