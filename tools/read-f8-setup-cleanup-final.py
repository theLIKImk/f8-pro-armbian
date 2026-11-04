import json,os,pwd,subprocess,stat
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
try:pwd.getpwnam('f8setup');exists=True
except KeyError:exists=False
archive=Path('/var/lib/f8-pro/retired-setup-r1')
p=Path('/var/lib/f8-pro/root-grow-r1a/complete.json')
out={'setup_account_exists':exists,'new_user_uid':pwd.getpwnam('likimk').pw_uid,'original_home_exists':Path('/home/f8setup').exists(),'archive_home_exists':(archive/'home').is_dir(),'archive_mode':oct(stat.S_IMODE(archive.stat().st_mode)),'setup_sudo_rule_exists':Path('/etc/sudoers.d/f8-first-run').exists(),'cleanup':json.loads((archive/'complete.json').read_text()),'root_grow':json.loads(p.read_text())}
for key,args in {'accounts_cache':['busctl','--system','call','org.freedesktop.Accounts','/org/freedesktop/Accounts','org.freedesktop.Accounts','ListCachedUsers'],'failed':['systemctl','--failed','--no-pager'],'space':['df','-B1','/']}.items():
 r=subprocess.run(args,text=True,capture_output=True,timeout=10);out[key]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
out['motor_active']=Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip()
assert not exists and out['archive_home_exists'] and not out['original_home_exists'] and not out['setup_sudo_rule_exists']
print(json.dumps(out,indent=2))
