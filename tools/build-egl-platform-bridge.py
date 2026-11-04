"""Build an isolated, test-scoped EGL platform-surface ABI bridge on the tablet."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
connection=importlib.util.module_from_spec(spec);spec.loader.exec_module(connection)
remote=connection.ssh('mktemp -d /home/alarm/f8-pro-builds/egl-platform-bridge-XXXXXXXX',
    capture_output=True,text=True,check=True,timeout=30).stdout.strip()
assert re.fullmatch(r'/home/alarm/f8-pro-builds/egl-platform-bridge-[A-Za-z0-9]{8}',remote)
source=ROOT/'tools/egl-platform-bridge.c'
subprocess.run(['scp',*connection.OPTIONS,str(source),connection.HOST+':'+remote+'/'],check=True,timeout=30)
script='cd '+remote+'\n'+r'''
set -eu
cc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Werror egl-platform-bridge.c \
 -o libf8-egl-platform.so -lEGL -ldl -pthread
sha256sum libf8-egl-platform.so
readelf -h libf8-egl-platform.so | grep Machine
'''
r=connection.ssh('sh -s',input=script,capture_output=True,text=True,timeout=60)
print(r.stdout+r.stderr)
r.check_returncode()
digest=re.search(r'^([0-9a-f]{64})  libf8-egl-platform.so$',r.stdout,re.M)[1]
out=ROOT/'outputs/weston-15.0.1';out.mkdir(parents=True,exist_ok=True)
subprocess.run(['scp',*connection.OPTIONS,connection.HOST+':'+remote+'/libf8-egl-platform.so',str(out/'libf8-egl-platform.so')],check=True,timeout=30)
assert hashlib.sha256((out/'libf8-egl-platform.so').read_bytes()).hexdigest()==digest
assert 'AArch64' in r.stdout
(ROOT/'analysis/weston-15.0.1/egl-platform-bridge.json').write_text(json.dumps({
    'remote_module':remote+'/libf8-egl-platform.so','sha256':digest,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'global_egl_modified':False,'scope':'Only preloaded into test Qt client; EGLAttrib values must fit EGLint.'},indent=2)+'\n')
