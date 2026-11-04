"""Exercise the real ARM64 helper inside the isolated root, then restore it."""
from pathlib import Path
import sys
import json,os,secrets,stat,subprocess
B=Path('/var/tmp/f8-pro-armbian/release-r1');R=B/'rootfs'
result_file=B/('first-run-native-test-r1a.json' if '--r1a' in sys.argv else 'first-run-native-test.json')
assert (B/'configured.json').exists();assert not result_file.exists()
assert R.resolve()==Path('/var/tmp/f8-pro-armbian/release-r1/rootfs')
names=['etc/passwd','etc/shadow','etc/group','etc/gshadow','etc/subuid','etc/subgid','etc/default/locale','etc/hostname','etc/hosts','etc/localtime','etc/timezone','etc/sddm.conf.d/99-f8-first-run.conf']
saved={}
for name in names:
 p=R/name
 if p.is_symlink():saved[name]=('link',os.readlink(p),p.lstat())
 elif p.exists():saved[name]=('file',p.read_bytes(),p.stat())
 else:saved[name]=('absent',None,None)
added_nodes=[]
for name,minor in [('null',3),('urandom',9)]:
 p=R/'dev'/name
 if not p.exists():os.mknod(p,stat.S_IFCHR|0o666,os.makedev(1,minor));added_nodes.append(p)
def cmd(args,**kw):return subprocess.run(['chroot',str(R),*args],check=True,capture_output=True,timeout=240,**kw)
results=[]
try:
 cmd(['/usr/sbin/visudo','-cf','/etc/sudoers.d/f8-first-run'])
 for auto in [False,True]:
  data=dict(username='f8qatest',fullname='F8 QA',password=secrets.token_urlsafe(18),locale='zh_CN.UTF-8',timezone='Asia/Hong_Kong',hostname='f8-qa-pad',autologin=auto)
  payload=json.dumps(data).encode()
  r=cmd(['/usr/bin/env','SUDO_USER=f8setup','/usr/local/lib/f8-pro/first-run-apply.py'],input=payload)
  assert json.loads(r.stdout)['ok']
  passwd=(R/'etc/passwd').read_text();account=next(x.split(':') for x in passwd.splitlines() if x.startswith('f8qatest:'))
  assert (R/'home/f8qatest/.config/plasmakeyboardrc').stat().st_uid==int(account[2])
  assert (R/'home/f8qatest/.config/systemd/user/graphical-session.target.wants/f8-cover-screen.service').is_symlink()
  assert 'f8setup:' in passwd and next(x for x in passwd.splitlines() if x.startswith('f8setup:')).endswith('/usr/sbin/nologin')
  assert ('User=f8qatest\n' if auto else 'User=\n') in (R/'etc/sddm.conf.d/99-f8-first-run.conf').read_text()
  status=cmd(['/usr/bin/passwd','--status','f8qatest']).stdout.decode();assert status.split()[1]=='P'
  duplicate=subprocess.run(['chroot',str(R),'/usr/bin/env','SUDO_USER=f8setup','/usr/local/lib/f8-pro/first-run-apply.py'],input=payload,capture_output=True,timeout=30)
  assert duplicate.returncode!=0
  results.append({'autologin':auto,'account_password_set':True,'new_home_defaults_owned_by_new_user':True,'setup_account_shell_disabled':True,'duplicate_rejected':True})
  cmd(['/usr/sbin/userdel','-r','f8qatest'])
  (R/'var/lib/f8-pro/first-run/complete.json').unlink()
  # Restore account state and defaults between both test modes.
  for name,(kind,body,info) in saved.items():
   p=R/name;p.unlink(missing_ok=True)
   if kind=='link':p.symlink_to(body)
   elif kind=='file':p.write_bytes(body);p.chmod(stat.S_IMODE(info.st_mode));os.chown(p,info.st_uid,info.st_gid)
finally:
 # Always restore even if the test fails. This is never the tablet's filesystem.
 subprocess.run(['chroot',str(R),'/usr/sbin/userdel','-r','f8qatest'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 (R/'var/lib/f8-pro/first-run/complete.json').unlink(missing_ok=True)
 for name,(kind,body,info) in saved.items():
  p=R/name;p.unlink(missing_ok=True)
  if kind=='link':p.symlink_to(body)
  elif kind=='file':p.write_bytes(body);p.chmod(stat.S_IMODE(info.st_mode));os.chown(p,info.st_uid,info.st_gid)
 for p in added_nodes:p.unlink()
 for name in ['passwd-','shadow-','group-','gshadow-','subuid-','subgid-']:(R/'etc'/name).unlink(missing_ok=True)
assert not (R/'home/f8qatest').exists()
assert not (R/'var/lib/f8-pro/first-run/complete.json').exists()
assert 'f8qatest' not in (R/'etc/passwd').read_text()
result_file.write_text(json.dumps({'arm64_chroot_actual_helper':True,'cases':results,'fixture_restored':True,'tablet_accounts_unchanged':True},indent=2)+'\n')
print('ARM64 first-run account integration tests passed')
