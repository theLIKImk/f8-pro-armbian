"""Install external build dependencies only after checking the complete sync plan."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('c',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('packages',nargs='+')
args=parser.parse_args()
family=set(json.loads((ROOT/'analysis/plasma-6.7.5/sources.json').read_text())['packages'])
for r in json.loads((ROOT/'analysis/plasma-6.7.5/recipe-dependencies.json').read_text())['recipes'].values():
    family.update(r['package_names'])
assert all(re.fullmatch(r'[a-z0-9][a-z0-9+_.-]*',p) and p not in family for p in args.packages)
payload='PACKAGES='+repr(args.packages)+'\nFAMILY='+repr(sorted(family))+'\n'+r'''
import subprocess
from pathlib import Path
assert not Path('/var/lib/pacman/db.lck').exists(),'pacman busy'
assert subprocess.check_output(['pacman-conf','--repo-list'],text=True).split()[0]=='f8-pro-plasma67'
subprocess.run(['pacman','-Sy','--noconfirm'],check=True)
plan=subprocess.check_output(['pacman','-Sup','--needed','--print-format','%n %v',*PACKAGES],text=True)
building=subprocess.run(['pgrep','-x','makepkg'],capture_output=True).returncode==0
for line in plan.splitlines():
    fields=line.split()
    if len(fields)!=2:continue
    name,version=fields
    if name in FAMILY:assert version.startswith('6.7.5-'),'Refusing mixed Plasma: '+line
    if building:
        old=subprocess.run(['pacman','-Q',name],capture_output=True,text=True)
        if old.returncode==0:assert old.stdout.split()==fields,'Defer existing-package upgrades while compiling: '+line
print('CHECKED EXTERNAL DEPENDENCY PLAN\n'+plan)
if plan.strip():
    subprocess.run(['pacman','-Su','--needed','--noconfirm',*PACKAGES],check=True)
subprocess.run(['systemctl','is-system-running'],check=True)
'''
r=c.ssh('sudo -n python3 -',input=payload,capture_output=True,text=True,timeout=900)
print(r.stdout[-12000:]+r.stderr[-2000:])
(ROOT/'analysis/plasma-6.7.5/last-external-deps.log').write_text(r.stdout+r.stderr)
r.check_returncode()
