import json,os,stat,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
helper=Path('/usr/lib/polkit-1/polkit-agent-helper-1')
assert helper.is_file() and not helper.is_symlink() and helper.stat().st_uid==0
owner=subprocess.check_output(['dpkg-query','-S',str(helper)],text=True).strip();assert owner.startswith('polkitd:')
base=Path('/var/lib/f8-pro/polkit-compat-20261102');base.mkdir(parents=True,exist_ok=True);base.chmod(0o700)
before={'mode':oct(stat.S_IMODE(helper.stat().st_mode)),'uid':helper.stat().st_uid,'gid':helper.stat().st_gid,'package':owner}
query=subprocess.run(['dpkg-statoverride','--list',str(helper)],text=True,capture_output=True)
before['statoverride']=query.stdout.strip()
marker=base/'before.json'
if not marker.exists():marker.write_text(json.dumps(before,indent=2)+'\n')
if query.returncode==0:
 fields=query.stdout.split();assert fields[:3] in [['root','root','4755'],['root','root','755']],'Unexpected administrator override'
 if fields[2]!='4755':subprocess.run(['dpkg-statoverride','--remove',str(helper)],check=True)
if not subprocess.run(['dpkg-statoverride','--list',str(helper)],stdout=subprocess.DEVNULL).returncode==0:
 subprocess.run(['dpkg-statoverride','--add','--update','root','root','4755',str(helper)],check=True)
else:os.chmod(helper,0o4755)
assert stat.S_IMODE(helper.stat().st_mode)==0o4755 and helper.stat().st_uid==0
# This old vendor kernel uses polkit's normal setuid fallback, not pidfd socket activation.
units=[p.name for p in Path('/usr/lib/systemd/system').glob('polkit-agent-helper*') if p.suffix in ['.socket','.service']]
if units:subprocess.run(['systemctl','mask','--now',*units],check=True,capture_output=True,timeout=15)
subprocess.run(['systemctl','add-wants','f8-desktop.target','ssh.service'],check=True,capture_output=True,timeout=15)
report={'helper_mode':oct(stat.S_IMODE(helper.stat().st_mode)),'persistent_override':subprocess.check_output(['dpkg-statoverride','--list',str(helper)],text=True).strip(),'masked_helper_units':units,'ssh_in_f8_target':Path('/etc/systemd/system/f8-desktop.target.wants/ssh.service').is_symlink(),'authentication_checks_bypassed':False,'time':time.time()}
(base/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print(subprocess.check_output(['runuser','-u','likimk','--','pw-record','--help'],text=True,stderr=subprocess.STDOUT))
