"""Back up and divert two distro plugins, install K1, verify user D-Bus IDs."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert subprocess.check_output(['dpkg-query','-W','-f=${Version}','ksystemstats'],text=True).startswith('6.6.6')
W=Path('/var/tmp/f8-pro-ksystemstats-k1');status=json.loads((W/'status.json').read_text());assert status['stage']=='built',status
directory=Path('/usr/lib/aarch64-linux-gnu/qt6/plugins/ksystemstats')
distribution=Path('/usr/lib/f8-pro/ksystemstats-distribution');distribution.mkdir(parents=True,exist_ok=True)
backup=Path('/var/lib/f8-pro/ksystemstats-k1');backup.mkdir(mode=0o700,parents=True,exist_ok=True)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
done=[];out={'plugins':{},'backup':str(backup)}
try:
 for kind in ['gpu','disk']:
  name='ksystemstats_plugin_'+kind+'.so';src=W/'output'/name;target=directory/name;divert=distribution/name
  assert digest(src)==status['plugins'][name]['sha256']
  assert not src.is_symlink() and not target.is_symlink()
  r=subprocess.run(['ldd','-r',str(src)],capture_output=True,text=True,timeout=10)
  assert r.returncode==0 and 'undefined symbol' not in r.stdout+r.stderr,(r.stdout,r.stderr)
  true=subprocess.check_output(['dpkg-divert','--truename',str(target)],text=True).strip()
  assert true in [str(target),str(divert)],'Unexpected existing diversion'
  if not (backup/(name+'.before')).exists():shutil.copy2(target,backup/(name+'.before'))
  if true==str(target):subprocess.run(['dpkg-divert','--local','--add','--rename','--divert',str(divert),str(target)],check=True,capture_output=True,timeout=10)
  done.append((target,divert))
  temp=target.with_name(name+'.f8-new');shutil.copyfile(src,temp);temp.chmod(0o644);os.chown(temp,0,0);os.replace(temp,target)
  out['plugins'][name]={'sha256':digest(target),'distribution_file':str(divert)}
 subprocess.run(u+['systemctl','--user','restart','plasma-ksystemstats.service'],check=True,capture_output=True,timeout=15)
 time.sleep(2)
 r=subprocess.run(u+['busctl','--user','--json=short','call','org.kde.ksystemstats1','/org/kde/ksystemstats1','org.kde.ksystemstats1','allSensors'],capture_output=True,text=True,timeout=15)
 assert r.returncode==0,(r.stdout,r.stderr)
 sensors=json.loads(r.stdout)['data'][0]
 ids=[s for s in sensors if s.startswith(('disk/','gpu/'))];out['sensor_ids']=sorted(ids)
 assert 'gpu/all/usage' in sensors,'Panthor GPU sensor not published'
 assert any(s.startswith('disk/') and not s.startswith('disk/all') and s.endswith('/used') for s in sensors),'eMMC volume sensor not published'
 out['installed']=True
except Exception as e:
 out['error']=str(e)
 for target,divert in reversed(done):
  if target.exists():target.unlink()
  subprocess.run(['dpkg-divert','--local','--remove','--rename','--divert',str(divert),str(target)],capture_output=True,timeout=10)
 subprocess.run(u+['systemctl','--user','restart','plasma-ksystemstats.service'],capture_output=True,timeout=15)
 out['installed']=False;out['rolled_back']=True
out['journal_tail']=subprocess.run(['journalctl','-b','--no-pager','--grep','ksystemstats','-n','20'],capture_output=True,text=True,timeout=10).stdout
(backup/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
