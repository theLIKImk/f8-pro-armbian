from pathlib import Path
import subprocess,json,re
B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2');R=B/'rootfs';image=B/'ROOTFS_F8_ARMBIAN_20261103_R2.ext4.img';P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-armbian-20261103-r2'
assert (B/'current-mkfs-complete.json').exists()
result={}
for n in ['/usr/bin/sudo','/usr/lib/polkit-1/polkit-agent-helper-1','/usr/local/lib/f8-pro/first-run-apply.py']:
 canonical=subprocess.check_output(['chroot',str(R),'/usr/bin/readlink','-f',n],text=True).strip()
 text=subprocess.check_output(['debugfs','-R','stat '+canonical,str(image)],text=True,stderr=subprocess.DEVNULL)
 mode=re.search(r'Mode:\s+([0-7]+)',text);owner=re.search(r'User:\s+(\d+)\s+Group:\s+(\d+)',text);assert mode and owner,text
 value=int(mode[1],8);assert owner[1]=='0' and owner[2]=='0';assert value&0o022==0
 if n!='/usr/local/lib/f8-pro/first-run-apply.py':assert value&0o4000,n
 result[n]={'resolved_path':canonical,'mode':oct(value),'uid':0,'gid':0}
r=subprocess.run(['chroot',str(R),'/usr/sbin/visudo','-c'],capture_output=True,text=True,timeout=20);assert r.returncode==0,r.stderr
(O/'privilege-modes.json').write_text(json.dumps({'actual_image_modes':result,'sudoers_syntax_passed':True},indent=2)+'\n');print(json.dumps({'actual_image_modes':result,'sudoers_syntax_passed':True}))
