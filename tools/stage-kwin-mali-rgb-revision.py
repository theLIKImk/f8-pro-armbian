"""Stage the opt-in legacy Mali RGB adapter in the idle existing KWin build."""
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
report=ROOT/'analysis/plasma-6.7.5'
m=json.loads((report/'kwin-mali-rgb-revision-migration.json').read_text());work=m['remote_build_directory']
assert re.fullmatch(r'/home/alarm/f8-pro-builds/kwin-6\.7\.5-[A-Za-z0-9]{8}',work)
recipe=ROOT/'packaging/plasma-6.7.5/kwin'
assert hashlib.sha256((recipe/'PKGBUILD').read_bytes()).hexdigest()==m['new_recipe_sha256']
assert hashlib.sha256((recipe/'f8-mali-buffer-sharing.patch').read_bytes()).hexdigest()==m['patch_sha256']
spec=importlib.util.spec_from_file_location('c',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
c.ssh('mkdir '+work+'/revision-3.4',check=True,timeout=20)
subprocess.run(['scp',*c.OPTIONS,str(recipe/'PKGBUILD'),str(recipe/'f8-mali-buffer-sharing.patch'),str(report/'kwin-mali-rgb-order-delta.patch'),
                c.HOST+':'+work+'/revision-3.4/'],check=True,timeout=30)
payload='M='+repr(m)+'\n'+r'''
from pathlib import Path
import hashlib,os,shutil,subprocess
assert os.getuid()==1000
assert subprocess.run(['pgrep','-x','makepkg'],capture_output=True).returncode==1
work=Path(M['remote_build_directory']);staged=work/'revision-3.4';source=work/'src/kwin-6.7.5'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(work/'PKGBUILD')==M['old_recipe_sha256']
assert digest(staged/'PKGBUILD')==M['new_recipe_sha256']
assert digest(staged/'f8-mali-buffer-sharing.patch')==M['patch_sha256']
assert digest(staged/'kwin-mali-rgb-order-delta.patch')==M['delta_sha256']
for relative,checks in M['sources'].items():
    assert relative in ('src/wayland/linuxdmabufv1clientbuffer.cpp','src/wayland/linuxdmabufv1clientbuffer_p.h')
    path=source/relative
    assert digest(path)==checks['old_sha256']
    backup=staged/(path.name+'.before-3.4');assert not backup.exists();shutil.copyfile(path,backup)
assert not (work/'PKGBUILD.before-3.4').exists()
shutil.copyfile(work/'PKGBUILD',work/'PKGBUILD.before-3.4')
with (staged/'kwin-mali-rgb-order-delta.patch').open('rb') as patch:
    subprocess.run(['patch','--fuzz=0','-d',str(source),'-p1'],stdin=patch,check=True)
for relative,checks in M['sources'].items():assert digest(source/relative)==checks['new_sha256']
shutil.copyfile(staged/'PKGBUILD',work/'PKGBUILD')
shutil.copyfile(staged/'f8-mali-buffer-sharing.patch',work/'f8-mali-buffer-sharing.patch')
assert digest(work/'PKGBUILD')==M['new_recipe_sha256']
print('KWIN_MALI_REVISION_3_4_STAGED; existing objects preserved; adapter remains opt-in')
'''
result=c.ssh('python3 -',input=payload,capture_output=True,text=True,timeout=30)
(report/'kwin-mali-rgb-revision-migration.log').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr);result.check_returncode()
