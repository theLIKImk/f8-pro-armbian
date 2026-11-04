"""Final credential/account scrub and auditable checks on a guarded offline root."""
from pathlib import Path
import os,re,json,shutil,hashlib
B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2');R=B/'rootfs'
assert B.parent.resolve()==Path('/var/tmp/f8-pro-armbian') and R.resolve()==B/'rootfs' and (B/'configured.json').exists()
for line in Path('/proc/self/mountinfo').read_text().splitlines():
 p=Path(line.split()[4]);assert p!=R and not p.is_relative_to(R)
removed=[]
def delete(p):
 assert p.is_relative_to(R) and p!=R
 if p.is_symlink() or p.is_file():p.unlink();removed.append(str(p.relative_to(R)))
 elif p.is_dir():shutil.rmtree(p);removed.append(str(p.relative_to(R)))
for n in ['etc/wpa_supplicant','etc/iwd','etc/connman','var/lib/iwd','var/lib/connman','var/lib/dhcp','var/lib/dhcpcd','etc/NetworkManager/system-connections','var/lib/NetworkManager','etc/apt/auth.conf','etc/apt/auth.conf.d','var/lib/AccountsService/users','var/lib/AccountsService/icons','var/lib/snapd/device','var/lib/snapd/cookie','var/lib/snapd/state.json.bak','var/lib/cloud','etc/sddm.f8-source']:
 delete(R/n)
for n in ['etc/NetworkManager/system-connections','var/lib/NetworkManager','etc/apt/auth.conf.d']:(R/n).mkdir(parents=True,exist_ok=True)
(R/'etc/NetworkManager/system-connections').chmod(0o700)
p=R/'etc/network/interfaces';p.parent.mkdir(exist_ok=True);p.write_text('auto lo\niface lo inet loopback\n')
for base,dirs,files in os.walk(R,followlinks=False):
 for n in list(dirs):
  if n=='.ssh':delete(Path(base)/n);dirs.remove(n)
 for n in files:
  p=Path(base)/n
  if n in ['authorized_keys','authorized_keys2','known_hosts','known_hosts.old','id_rsa','id_ed25519','id_ecdsa','id_dsa','.bash_history','.zsh_history','.python_history'] or n.startswith('ssh_host_'):delete(p)
for p in (R/'etc/systemd/system').glob('*.wants/*'):
 if p.name in ['ssh.service','ssh.socket','sshd.service','f8-live-ssh.service']:delete(p)
for n in ['etc/systemd/system/f8-live-ssh.service','usr/libexec/f8-pro/live-ssh.sh','usr/libexec/f8-pro/f8-live-ssh.sh','usr/share/f8-pro/test-authorized-keys']:delete(R/n)
# Recreate secret-free persistent daemon directories with distribution account ownership.
rows=[line.split(':') for line in (R/'etc/passwd').read_text().splitlines()]
for user in ['_chrony','chrony']:
 matches=[x for x in rows if x[0]==user]
 if matches:
  p=R/'var/lib/chrony';p.mkdir(parents=True,exist_ok=True);os.chown(p,int(matches[0][2]),int(matches[0][3]));p.chmod(0o750);break
# Remove account-specific sudo grants left by any earlier testing setup.
for p in (R/'etc/sudoers.d').glob('*'):
 if p.is_file() and p.name!='f8-first-run':
  text=p.read_text(errors='replace')
  if re.search(r'(?m)^\s*(?:likimk|f8test|f8gpu|f8qatest|f8qadiag)\s',text):delete(p)
# Only the initial graphical setup account may remain among normal users.
users=[line.split(':') for line in (R/'etc/passwd').read_text().splitlines()]
assert [u[0] for u in users if 1000<=int(u[2])<60000]==['f8setup']
assert all(line.split(':')[1]=='*' for line in (R/'etc/shadow').read_text().splitlines())
assert sorted(p.name for p in (R/'home').iterdir())==['f8setup']
assert not list((R/'etc/ssh').glob('ssh_host_*'))
assert not list((R/'etc/NetworkManager/system-connections').iterdir())
assert sorted(p.name for p in (R/'etc/netplan').iterdir())==['00-default-use-network-manager.yaml']
for b in ['home','root','etc/skel','var/lib']:
 assert not list((R/b).rglob('.ssh'))
for n in ['etc/skel/.config/fcitx5/conf/pinyin.conf','home/f8setup/.config/fcitx5/conf/pinyin.conf']:assert 'CloudPinyinEnabled=True' in (R/n).read_text()
for n in ['etc/skel/.config/fcitx5/conf/cloudpinyin.conf','home/f8setup/.config/fcitx5/conf/cloudpinyin.conf']:assert 'Backend=Baidu' in (R/n).read_text()
# Operational configuration must contain no private-key material or wireless PSKs.
violations=[]
for b in ['etc','home','root','usr/local/lib/f8-pro','usr/libexec/f8-pro']:
 for base,dirs,files in os.walk(R/b,followlinks=False):
  for n in files:
   p=Path(base)/n
   if p.is_symlink() or p.stat().st_size>8*1024**2:continue
   data=p.read_bytes()
   if any(v in data for v in [b'-----BEGIN OPENSSH PRIVATE KEY-----',b'-----BEGIN RSA PRIVATE KEY-----',b'-----BEGIN PRIVATE KEY-----']) or re.search(rb'(?im)^\s*(?:psk|wpa-psk|wep-key[0-3])\s*=\s*[^\s#]+',data):violations.append(str(p.relative_to(R)))
assert not violations,violations
# No first-run completion identity and no shared gyro calibration should be shipped.
assert not (R/'var/lib/f8-pro/first-run/complete.json').exists()
for p in R.rglob('f8-gyro-bias.json'):raise AssertionError(str(p))
record={'wifi_profiles_empty':True,'wireless_psk_scan_clean':True,'ssh_host_keys_absent':True,'ssh_user_keys_and_known_hosts_absent':True,'ssh_opt_in':True,'all_shadow_hashes_locked':True,'only_setup_user':True,'personal_homes_absent':True,'private_key_scan_clean':True,'cloudpinyin_default_enabled':True,'removed_paths':removed,'staging_root':str(R)}
(B/'privacy-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='removed_paths'}))
