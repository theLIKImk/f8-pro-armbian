"""Build a process-local observer of Wayland global protocol definitions."""
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('c',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
work=c.ssh('mktemp -d /home/alarm/f8-pro-builds/mali-protocol-trace-XXXXXXXX',check=True,capture_output=True,text=True,timeout=30).stdout.strip()
assert re.fullmatch(r'/home/alarm/f8-pro-builds/mali-protocol-trace-[A-Za-z0-9]{8}',work)
source=ROOT/'tools/trace-mali-protocol.c'
subprocess.run(['scp',*c.OPTIONS,str(source),c.HOST+':'+work+'/'],check=True,timeout=30)
result=c.ssh('cd '+work+' && cc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Werror trace-mali-protocol.c -o libf8-mali-protocol-trace.so -ldl -pthread && sha256sum libf8-mali-protocol-trace.so',capture_output=True,text=True,timeout=30)
print(result.stdout+result.stderr);result.check_returncode()
digest=re.fullmatch(r'([0-9a-f]{64})  libf8-mali-protocol-trace.so\n',result.stdout)[1]
(ROOT/'analysis/arch-gpu/mali-protocol-trace.json').write_text(json.dumps({'remote_module':work+'/libf8-mali-protocol-trace.so','sha256':digest,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Weston process only; public wl_global_create metadata observer'},indent=2)+'\n')
