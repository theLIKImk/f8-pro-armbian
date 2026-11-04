"""Read-only checks before the bounded native KWin graphics test."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import tarfile

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
reports=ROOT/'analysis/plasma-6.7.5'
kwin=json.loads((reports/'kwin-native-build.json').read_text())
assert kwin['arm64_package_built'] and kwin['package_installed']
version=kwin['package'].removeprefix('kwin-').split('-aarch64.pkg.tar.')[0]
assert re.fullmatch(r'6\.7\.5-\d+\.\d+',version)
bridge=json.loads((ROOT/'analysis/weston-15.0.1/egl-platform-bridge.json').read_text())
theme=json.loads((reports/'plasma-integration-native-build.json').read_text())
assert theme['arm64_package_built']
archive=ROOT/'outputs/plasma-6.7.5'/theme['package']
assert hashlib.sha256(archive.read_bytes()).hexdigest()==theme['package_sha256']
relative='usr/lib/qt6/plugins/platformthemes/KDEPlasmaPlatformTheme6.so'
with tarfile.open(archive) as package:
    theme_sha=hashlib.sha256(package.extractfile(relative).read()).hexdigest()
checks={bridge['remote_module']:bridge['sha256'],
        theme['remote_build_directory']+'/pkg/plasma-integration/'+relative:theme_sha}
assert all(re.fullmatch(r'/home/alarm/f8-pro-builds/[A-Za-z0-9./_-]+',p) and '..' not in p for p in checks)
payload='EXPECTED_VERSION='+repr(version)+'\nCHECKS='+repr(checks)+'\n'+r'''
from pathlib import Path
import hashlib,json,os,subprocess
assert os.getuid()==1000
errors=[]
actual=subprocess.check_output(['pacman','-Q','kwin'],text=True).strip()
if actual!='kwin '+EXPECTED_VERSION:errors.append('Installed KWin version differs from reviewed package')
binary=Path('/usr/bin/kwin_wayland')
header=binary.read_bytes()[:20]
if header[:6]!=b'\x7fELF\x02\x01' or int.from_bytes(header[18:20],'little')!=183:
    errors.append('KWin is not an ARM64 executable')
caps=subprocess.run(['getcap',str(binary)],capture_output=True,text=True,check=True).stdout.strip()
if caps:errors.append('KWin file capabilities would affect private loader environment')
for name,digest in CHECKS.items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:errors.append('Private module hash differs: '+name)
environment=dict(os.environ,LD_LIBRARY_PATH='/opt/f8-pro/vendor-gpu-g13p0-20261028/lib')
environment.pop('LD_PRELOAD',None)
libraries=subprocess.run(['ldd',str(binary)],env=environment,capture_output=True,text=True,check=True).stdout
if 'not found' in libraries:errors.append('Unresolved KWin dynamic library')
for unit in ['display-manager.service','getty@tty7.service']:
    if subprocess.run(['systemctl','is-active','--quiet',unit]).returncode==0:
        errors.append('Test terminal or display manager already active: '+unit)
temperatures={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
if not temperatures or max(temperatures.values())>=70000:errors.append('Wait for temperature below70C before graphics test')
record={'installed_package':actual,'arm64_executable':not any('ARM64' in x for x in errors),
        'file_capabilities':caps,'private_module_sha256':CHECKS,'dynamic_libraries':libraries,
        'temperatures_milli_celsius':temperatures,'errors':errors,'ready':not errors,
        'scope':'Read-only prerequisite checks; not graphics acceptance'}
print(json.dumps(record,indent=2))
raise SystemExit(0 if not errors else 3)
'''
result=c.ssh('python3 -',input=payload,capture_output=True,text=True,timeout=45)
(reports/'kwin-wayland-preflight.log').write_text(result.stdout+result.stderr)
if result.stdout:
    record=json.loads(result.stdout)
    (reports/'kwin-wayland-preflight.json').write_text(json.dumps(record,indent=2)+'\n')
if result.stdout:
    print(json.dumps({key:value for key,value in record.items() if key!='dynamic_libraries'},indent=2))
if result.stderr:print(result.stderr)
result.check_returncode()
