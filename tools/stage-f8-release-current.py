"""Read-only live snapshot into a guarded private offline release root.
Credentials arrive only via stdin and are kept in process memory/environment.
"""
from pathlib import Path
import json,os,subprocess,shlex,time,sys,tarfile
P=Path(__file__).resolve().parents[1];B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2');R=B/'rootfs'
assert B.parent.resolve()==Path('/var/tmp/f8-pro-armbian') and B.name=='release-20261103-r2'
B.mkdir(mode=0o700,exist_ok=True);assert not (B/'snapshot-complete.json').exists();assert not R.exists(),'Inspect an incomplete snapshot before retrying'
R.mkdir();data=json.load(sys.stdin);password=data.pop('password');assert '\n' not in password
known=Path('/var/tmp/f8-pro-armbian/post-wizard-likimk/known_hosts');assert known.exists()
assert 'SHA256:XS9mqNQLlia6AOakeRu4osWr1oDrnd5oCejmQ3jbeGU' in subprocess.check_output(['ssh-keygen','-lf',str(known)],text=True)
env=dict(os.environ,SSHPASS=password)
ssh=['sshpass','-e','ssh','-T','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=8',data['username']+'@'+data['address']]
def progress(phase,**kw):
 v={'phase':phase,'time':time.time(),**kw};(B/'progress.json').write_text(json.dumps(v)+'\n');print(json.dumps(v),flush=True)
def remote(args,output):
 cmd='sudo -S -p '+shlex.quote('')+' '+shlex.join(args)
 with output.open('wb') as f,(B/(output.name+'.stderr')).open('wb') as e:
  p=subprocess.Popen(ssh+[cmd],stdin=subprocess.PIPE,stdout=f,stderr=e,env=env);p.stdin.write(password.encode()+b'\n');p.stdin.close();rc=p.wait()
 assert rc==0,(args[:2],rc)
# Root snapshot excludes identities and personal writable state before any data crosses the network.
excludes=['dev','proc','sys','run','tmp','mnt','media','home','root','lost+found','etc/shadow','etc/shadow-','etc/gshadow','etc/gshadow-','etc/ssh','etc/NetworkManager/system-connections','etc/netplan','etc/wpa_supplicant','etc/iwd','etc/connman','etc/network/interfaces.d','etc/ssl/private','etc/credstore','etc/credstore.encrypted','etc/wireguard','etc/apt/auth.conf','etc/apt/auth.conf.d','var/cache','var/log','var/log.hdd','var/crash','var/tmp','var/backups','var/spool','var/mail','var/lib/NetworkManager','var/lib/bluetooth','var/lib/iwd','var/lib/connman','var/lib/sddm','var/lib/f8-pro','var/lib/systemd/random-seed','var/lib/systemd/credential.secret','var/lib/AccountsService/users','var/lib/AccountsService/icons','var/lib/dhcp','var/lib/dhcpcd','var/lib/chrony','var/lib/private','var/lib/sss','var/lib/avahi-autoipd','var/lib/colord','var/lib/cups','var/lib/snapd/device','var/lib/snapd/cookie','var/lib/snapd/state.json','var/lib/snapd/state.json.bak']
args=['/usr/bin/tar','--one-file-system','--numeric-owner','--acls','--xattrs','--ignore-failed-read','--warning=no-file-changed',*['--exclude=./'+x for x in excludes],'-C','/','-cpf','-','.']
progress('copying_rootfs')
cmd='sudo -S -p '+shlex.quote('')+' '+shlex.join(args)
with (B/'snapshot.stderr').open('wb') as e,(B/'extract.log').open('wb') as el:
 source=subprocess.Popen(ssh+[cmd],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=e,env=env)
 target=subprocess.Popen(['tar','--numeric-owner','--acls','--xattrs','-xpf','-','-C',str(R)],stdin=source.stdout,stdout=el,stderr=el)
 source.stdout.close();source.stdin.write(password.encode()+b'\n');source.stdin.close()
 rc=source.wait();trc=target.wait()
 assert rc in [0,1] and trc==0,(rc,trc)
progress('reading_validated_boot')
remote(['/usr/bin/dd','if=/dev/mmcblk0p3','bs=1048576','status=none'],B/'BOOT_CURRENT_PARTITION.img')
assert (B/'BOOT_CURRENT_PARTITION.img').stat().st_size==64*1024**2
# Account-specific transport only for the small documented defaults allowlist.
assets=['.config/kwinrc','.config/plasmakeyboardrc','.config/kscreenlockerrc','.config/f8-cover.json','.config/systemd/user/f8-cover-screen.service']
remote(['/usr/bin/tar','--ignore-failed-read','-C','/home/'+data['username'],'-cpf','-',*assets],B/'user-defaults.tar')
D=B/'user-defaults';D.mkdir()
with tarfile.open(B/'user-defaults.tar') as t:
 for i in t.getmembers():
  assert i.name in assets and i.isfile();p=D/i.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(i).read())
# Keep installed Snap app versions, excluding store credentials/device identity/tasks.
code="import json;from pathlib import Path;p=Path('/var/lib/snapd/state.json');d=json.loads(p.read_text()) if p.exists() else {};data=d.get('data',{});safe={k:v for k,v in data.items() if k not in ['auth','device','device-identity','device-keypair','auth-users','users'] and not any(s in k.lower() for s in ['macaroon','token','password','secret'])};print(json.dumps({'data':safe,'changes':{},'tasks':{},**{k:v for k,v in d.items() if k.startswith('last-')}}))"
remote(['/usr/bin/python3','-I','-c',code],B/'snap-state-sanitized.json')
snap=R/'var/lib/snapd/state.json';snap.parent.mkdir(parents=True,exist_ok=True);snap.write_bytes((B/'snap-state-sanitized.json').read_bytes());snap.chmod(0o600)
metadata={'time':time.time(),'root':str(R),'excludes':excludes,'user_allowlist':assets,'source_is_live_file_copy':True,'target_device_writes':False,'boot_partition_bytes':64*1024**2,'source_account':data['username']}
(B/'snapshot-complete.json').write_text(json.dumps(metadata,indent=2)+'\n');env.pop('SSHPASS',None);password=None
progress('snapshot_complete')
