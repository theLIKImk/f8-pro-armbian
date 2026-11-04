"""Maintain a priority local repository of reviewed 6.7.5 builds, with transaction preflight."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--install',nargs='*',default=[])
args=parser.parse_args()
records=[]
reports=ROOT/'analysis/plasma-6.7.5'
for f in reports.glob('*-native-build.json'):
    r=json.loads(f.read_text());name=f.name.removesuffix('-native-build.json')
    if not r.get('arm64_package_built'):continue
    origin=json.loads((ROOT/'packaging/plasma-6.7.5'/name/'origin.json').read_text())
    path=ROOT/'outputs/plasma-6.7.5'/r['package']
    assert origin['built'] and (r['elf_architecture_checked'] or
        (origin.get('data_only') and r.get('data_only') and not r['elf_architecture_checked']))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==r['package_sha256']==origin['package_sha256']
    records.append({'name':name,'file':r['package'],'path':r['remote_build_directory']+'/'+r['package'],
                    'sha256':r['package_sha256'],'version':r['package'][len(name)+1:].split('-'+r.get('package_architecture','aarch64')+'.pkg.tar.')[0],
                    'report_owner':name})
    for extra in r.get('additional_artifacts',[]):
        data_name=extra['package_name'];assert extra['data_only'] and data_name in origin['data_packages']
        assert extra['package_sha256']==origin['additional_package_sha256'][data_name]
        file=ROOT/'outputs/plasma-6.7.5'/extra['package']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==extra['package_sha256']
        records.append({'name':data_name,'file':extra['package'],'path':r['remote_build_directory']+'/'+extra['package'],
                        'sha256':extra['package_sha256'],'version':extra['package'][len(data_name)+1:].split('-aarch64.pkg.tar.')[0],
                        'report_owner':name})
assert set(args.install)<={r['name'] for r in records}
release=set(json.loads((reports/'sources.json').read_text())['packages'])
for r in json.loads((reports/'recipe-dependencies.json').read_text())['recipes'].values():
    release.update(r['package_names'])
payload='RECORDS='+repr(records)+'\nINSTALL='+repr(args.install)+'\nRELEASE='+repr(sorted(release))+'\n'+r'''
from pathlib import Path
import hashlib,os,re,shutil,subprocess,json
assert os.getuid()==0
assert not Path('/var/lib/pacman/db.lck').exists(),'pacman busy'
assert shutil.which('repo-add'),'repo-add missing; configuration unchanged'
repo=Path('/var/lib/f8-pro/packages/plasma-6.7.5')
repo.mkdir(parents=True,mode=0o755,exist_ok=True)
for r in RECORDS:
    source=Path(r['path']).resolve()
    assert source.is_relative_to('/home/alarm/f8-pro-builds')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256']
    assert subprocess.check_output(['pacman','-Qp',str(source)],text=True).split()==[r['name'],r['version']]
    target=repo/r['file']
    if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==r['sha256'],'Bump pkgrel instead of replacing a different package'
    else:shutil.copyfile(source,target);target.chmod(0o644)
subprocess.run(['repo-add',str(repo/'f8-pro-plasma67.db.tar.gz'),*[str(repo/r['file']) for r in RECORDS]],check=True)
config=Path('/etc/pacman.conf');text=config.read_text()
section='[f8-pro-plasma67]\nSigLevel = Optional\nServer = file:///var/lib/f8-pro/packages/plasma-6.7.5\n\n'
if '[f8-pro-plasma67]' not in text:
    backup=Path('/var/lib/f8-pro/maintenance/pacman.conf.before-f8-plasma67')
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copyfile(config,backup);backup.chmod(0o600)
    match=re.search(r'^\[(?!options\])[^\]]+\]',text,re.M)
    assert match,'Cannot locate standard repositories'
    temporary=config.with_suffix('.f8-new')
    temporary.write_text(text[:match.start()]+section+text[match.start():])
    temporary.chmod(0o644);temporary.replace(config)
else:assert section.strip() in text,'Existing repository configuration differs'
repos=subprocess.check_output(['pacman-conf','--repo-list'],text=True).split()
assert repos[0]=='f8-pro-plasma67',repos
sync=Path('/var/lib/pacman/sync/f8-pro-plasma67.db')
temporary=sync.with_suffix('.new')
shutil.copyfile(repo/'f8-pro-plasma67.db.tar.gz',temporary)
temporary.chmod(0o644);temporary.replace(sync)
selected=[r for r in RECORDS if r['name'] in INSTALL]
targets=[str(repo/r['file']) for r in selected]
plan=subprocess.check_output(['pacman','-Up','--print-format','%n %v',*targets],text=True) if INSTALL else ''
planned=[]
for line in plan.splitlines():
    fields=line.split()
    if len(fields)==2:planned.append(fields[0])
    if len(fields)==2 and fields[0] in RELEASE:
        assert fields[1].startswith('6.7.5-'),'Refusing mixed Plasma transaction: '+line
print('REVIEWED TRANSACTION\n'+plan)
if INSTALL:
    assert set(planned)==set(INSTALL),'Refusing additional package changes'
    subprocess.run(['pacman','-U','--needed','--noconfirm',*targets],check=True)
    for name in INSTALL:
        r=next(x for x in RECORDS if x['name']==name)
        assert subprocess.check_output(['pacman','-Q',name],text=True).split()==[name,r['version']]
subprocess.run(['systemctl','is-system-running'],check=True)
print('LOCAL_REPOSITORY_AND_VERSION_CHECKS_PASS')
'''
r=c.ssh('sudo -n python3 -',input=payload,capture_output=True,text=True,timeout=240)
(reports/'local-repository.log').write_text(r.stdout+r.stderr)
print(r.stdout[-12000:]+r.stderr[-2000:]);r.check_returncode()
(reports/'local-repository.json').write_text(json.dumps({'name':'f8-pro-plasma67','target_directory':'/var/lib/f8-pro/packages/plasma-6.7.5','priority_first':True,'signature_policy':'Optional only for this local source-verified build repository; distro repository signature policies unchanged','packages':records,'installed_this_run':args.install,'preflight_rejects_other_plasma_versions':True},indent=2)+'\n')
for owner in {r['report_owner'] for r in records if r['name'] in args.install}:
    f=reports/(owner+'-native-build.json');r=json.loads(f.read_text())
    if owner in args.install:r['package_installed']=True
    for extra in r.get('additional_artifacts',[]):
        if extra['package_name'] in args.install:extra['package_installed']=True
    f.write_text(json.dumps(r,indent=2)+'\n')
