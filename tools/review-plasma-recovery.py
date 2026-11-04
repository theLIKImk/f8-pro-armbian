from pathlib import Path
import json,importlib.util
p=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
s=importlib.util.spec_from_file_location('c',p/'tools/build-plasma-activities.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
records=[]
for name in ('plasma-activities','layer-shell-qt','knighttime','kwayland'):
 r=json.loads((p/'analysis/plasma-6.7.5'/(name+'-native-build.json')).read_text());records.append({'name':name,'path':r['remote_build_directory']+'/'+r['package'],'sha256':r['package_sha256']})
payload='RECORDS='+repr(records)+'\n'+r'''
import subprocess,hashlib,shutil
from pathlib import Path
for r in RECORDS:
 assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']
 print('CURRENT '+subprocess.check_output(['pacman','-Q',r['name']],text=True).strip())
print('PLANNED LOCAL FILE TRANSACTION')
subprocess.run(['pacman','-Up','--print-format','%n %v',*[r['path'] for r in RECORDS]],check=True)
print('REPO_ADD_PRESENT',bool(shutil.which('repo-add')))
print('REPOSITORY_ORDER')
subprocess.run(['pacman-conf','--repo-list'],check=True)
'''
r=c.ssh('python3 -',input=payload,capture_output=True,text=True,timeout=45)
print(r.stdout+r.stderr);r.check_returncode();(p/'analysis/plasma-6.7.5/recovery-readonly-preflight.log').write_text(r.stdout+r.stderr)
