"""Install upstream Phira's native Linux text-dialog dependency."""
import json,os,subprocess
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
base=['apt-get','-o','Dpkg::Use-Pty=0']
dry=subprocess.run(base+['--simulate','--no-install-recommends','install','zenity'],capture_output=True,text=True,timeout=30)
assert dry.returncode==0,dry.stderr
assert not any(l.startswith('Remv ') for l in dry.stdout.splitlines()),'Unexpected removals'
assert not any(l.startswith('Inst ') and ' [' in l for l in dry.stdout.splitlines()),'Unexpected upgrades'
r=subprocess.run(base+['-y','--no-install-recommends','install','zenity'],env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),capture_output=True,text=True,timeout=60)
print(json.dumps({'exit':r.returncode,'plan':dry.stdout,'stdout':r.stdout[-12000:],'stderr':r.stderr[-3000:]}));assert r.returncode==0
