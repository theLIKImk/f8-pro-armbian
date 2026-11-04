import json,os,subprocess,shutil
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
out={}
def cmd(k,args):
 try:
  r=subprocess.run(args,capture_output=True,text=True,timeout=12);out[k]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:out[k]={'error':str(e)}
cmd('packages',['dpkg-query','-W','plasma-systemmonitor','ksystemstats','libksysguard-data','udisks2','smartmontools'])
cmd('user_service',u+['systemctl','--user','status','plasma-ksystemstats.service','--no-pager'])
cmd('processes',['pgrep','-af','ksystemstats|plasma-systemmonitor'])
cmd('journal',['journalctl','-b','--no-pager','--grep','ksystemstats|ksysguard|systemmonitor','-n','100'])
cmd('bus',u+['busctl','--user','list'])
cmd('plugins',['dpkg-query','-L','ksystemstats'])
cmd('disks',['lsblk','-o','NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS'])
out['diskstats']=Path('/proc/diskstats').read_text()
out['drm']={}
for p in Path('/sys/class/drm').glob('card[0-9]'):
 d=p/'device';out['drm'][p.name]={'device':str(d.resolve()),'driver':str((d/'driver').resolve()),'uevent':(d/'uevent').read_text() if (d/'uevent').exists() else '', 'files':[x.name for x in d.iterdir()]}
out['gpu']={p.name:{n:(p/n).read_text().strip() for n in ['cur_freq','min_freq','max_freq','load','busy_time','total_time'] if (p/n).exists()} for p in Path('/sys/class/devfreq').glob('*gpu*')}
print(json.dumps(out,indent=2))
