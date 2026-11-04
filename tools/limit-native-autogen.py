"""Limit AUTOGEN in an existing, idle reviewed native build cache."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package',choices=['kwin','kactivitymanagerd'],required=True)
args=parser.parse_args()
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
report=ROOT/'analysis/plasma-6.7.5'
status=json.loads((report/(args.package+'-native-build.json')).read_text())
assert not status['arm64_package_built'],'Use the recipe for new builds; preserve completed artifact provenance'
work=status['remote_build_directory']
assert re.fullmatch('/home/alarm/f8-pro-builds/'+re.escape(args.package)+r'-6\.7\.5-[A-Za-z0-9]{8}',work)
payload='WORK='+repr(work)+'\nNAME='+repr(args.package)+'\n'+r'''
from pathlib import Path
import json,os,shutil,subprocess
assert os.getuid()==1000
assert subprocess.run(['pgrep','-x','makepkg'],capture_output=True).returncode==1,'A build is active'
work=Path(WORK)
build=work/'src/build';source=work/'src'/(NAME+'-6.7.5')
assert (source/'CMakeLists.txt').is_file() and (build/'CMakeCache.txt').is_file()
backup=work/'CMakeCache.before-autogen-limit.txt'
if not backup.exists():shutil.copyfile(build/'CMakeCache.txt',backup)
before=sorted({json.loads(p.read_text())['PARALLEL'] for p in build.rglob('AutogenInfo.json')})
with (work/'autogen-limit-configure.log').open('w') as output:
    subprocess.run(['cmake','-S',str(source),'-B',str(build),'-DCMAKE_AUTOGEN_PARALLEL=1'],
                   stdout=output,stderr=subprocess.STDOUT,check=True,timeout=60)
values=[json.loads(p.read_text())['PARALLEL'] for p in build.rglob('AutogenInfo.json')]
assert values and set(values)=={1}
result={'package':NAME,'setting':'CMAKE_AUTOGEN_PARALLEL','before_values':before,'after':1,
        'verified_autogen_targets':len(values),'scope':'Only native build cache; source and PKGBUILD unchanged'}
(work/'autogen-limit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
'''
result=c.ssh('python3 -',input=payload,capture_output=True,text=True,timeout=90)
(report/(args.package+'-autogen-limit-console.log')).write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
result.check_returncode()
(report/(args.package+'-autogen-limit.json')).write_text(json.dumps(json.loads(result.stdout),indent=2)+'\n')
