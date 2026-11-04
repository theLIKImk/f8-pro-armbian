"""Migrate the idle 3.1 build to reviewed 3.2 without losing compiled objects."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
report=ROOT/'analysis/plasma-6.7.5'
m=json.loads((report/'kwin-glsl-revision-migration.json').read_text())
work=m['remote_build_directory']
assert re.fullmatch(r'/home/alarm/f8-pro-builds/kwin-6\.7\.5-[A-Za-z0-9]{8}',work)
recipe=ROOT/'packaging/plasma-6.7.5/kwin'
assert hashlib.sha256((recipe/'PKGBUILD').read_bytes()).hexdigest()==m['new_recipe_sha256']
assert hashlib.sha256((recipe/'f8-glsl-defined-guard.patch').read_bytes()).hexdigest()==m['patch_sha256']
spec=importlib.util.spec_from_file_location('c',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
c.ssh('mkdir '+work+'/revision-3.2',check=True,timeout=20)
subprocess.run(['scp',*c.OPTIONS,str(recipe/'PKGBUILD'),str(recipe/'f8-glsl-defined-guard.patch'),
                c.HOST+':'+work+'/revision-3.2/'],check=True,timeout=30)
payload='M='+repr(m)+'\n'+r'''
from pathlib import Path
import hashlib,os,shutil,subprocess,json
assert os.getuid()==1000
assert subprocess.run(['pgrep','-x','makepkg'],capture_output=True).returncode==1,'Build still active'
work=Path(M['remote_build_directory']);staged=work/'revision-3.2'
shader=work/'src/kwin-6.7.5/src/opengl/base.frag'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(work/'PKGBUILD')==M['old_recipe_sha256']
assert digest(shader)==M['old_shader_sha256']
assert digest(staged/'PKGBUILD')==M['new_recipe_sha256']
assert digest(staged/'f8-glsl-defined-guard.patch')==M['patch_sha256']
for source,name in [(work/'PKGBUILD','PKGBUILD.before-3.2'),(shader,'base.frag.before-3.2')]:
    assert not (work/name).exists()
    shutil.copyfile(source,work/name)
with (staged/'f8-glsl-defined-guard.patch').open('rb') as patch:
    subprocess.run(['patch','--fuzz=0','-d',str(work/'src/kwin-6.7.5'),'-p1'],stdin=patch,check=True)
assert digest(shader)==M['new_shader_sha256']
shutil.copyfile(staged/'PKGBUILD',work/'PKGBUILD')
shutil.copyfile(staged/'f8-glsl-defined-guard.patch',work/'f8-glsl-defined-guard.patch')
assert digest(work/'PKGBUILD')==M['new_recipe_sha256']
print('KWIN_GLSL_REVISION_3_2_STAGED; existing objects preserved')
'''
result=c.ssh('python3 -',input=payload,capture_output=True,text=True,timeout=30)
(report/'kwin-glsl-revision-migration.log').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
result.check_returncode()
