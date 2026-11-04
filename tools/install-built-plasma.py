"""Install selected reviewed native packages after local and target hash checks."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('packages',nargs='+',choices=['plasma-activities','layer-shell-qt','knighttime','kwayland','kdecoration'])
args=parser.parse_args()
records=[]
for name in args.packages:
    report=ROOT/'analysis/plasma-6.7.5'/(name+'-native-build.json')
    r=json.loads(report.read_text());origin=json.loads((ROOT/'packaging/plasma-6.7.5'/name/'origin.json').read_text())
    assert r['arm64_package_built'] and r['elf_architecture_checked'] and origin['built']
    path=ROOT/'outputs/plasma-6.7.5'/r['package']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==r['package_sha256']==origin['package_sha256']
    version=r['package'][len(name)+1:].split('-aarch64.pkg.tar.')[0]
    records.append({'name':name,'version':version,'path':r['remote_build_directory']+'/'+r['package'],'sha256':r['package_sha256']})
payload='RECORDS='+repr(records)+'\n'+r'''
from pathlib import Path
import datetime,hashlib,subprocess,json,os
assert os.getuid()==0
assert not Path('/var/lib/pacman/db.lck').exists(),'Package transaction already active'
for r in RECORDS:
    p=Path(r['path']).resolve()
    assert p.is_relative_to('/home/alarm/f8-pro-builds') and p.is_file()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    metadata=subprocess.check_output(['pacman','-Qp',str(p)],text=True).split()
    assert metadata==[r['name'],r['version']],metadata
    old=subprocess.run(['pacman','-Q',r['name']],capture_output=True,text=True)
    if old.returncode==0:assert old.stdout.split()==metadata,'Refusing unexpected replacement'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=Path('/var/lib/f8-pro/maintenance')/('before-plasma-packages-'+stamp)
backup.mkdir(parents=True,mode=0o700)
(backup/'installed-packages.txt').write_text(subprocess.check_output(['pacman','-Q'],text=True))
(backup/'requested.json').write_text(json.dumps(RECORDS,indent=2)+'\n')
subprocess.run(['pacman','-U','--needed','--noconfirm',*[r['path'] for r in RECORDS]],check=True)
for r in RECORDS:
    assert subprocess.check_output(['pacman','-Q',r['name']],text=True).split()==[r['name'],r['version']]
    print(r['name']+' '+r['version']+' INSTALLED')
subprocess.run(['systemctl','is-system-running'],check=True)
'''
r=c.ssh('sudo -n python3 -',input=payload,capture_output=True,text=True,timeout=180)
print(r.stdout+r.stderr)
(ROOT/'analysis/plasma-6.7.5/last-local-install.log').write_text(r.stdout+r.stderr)
r.check_returncode()
for name in args.packages:
    f=ROOT/'analysis/plasma-6.7.5'/(name+'-native-build.json');r=json.loads(f.read_text());r['package_installed']=True;f.write_text(json.dumps(r,indent=2)+'\n')
