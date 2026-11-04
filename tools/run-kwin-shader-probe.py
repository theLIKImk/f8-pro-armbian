"""Run the exact failed GLSL source in a tiny offscreen Mali context."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('c',ROOT/'tools/build-plasma-activities.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
evidence=ROOT/'analysis/arch-gpu/kwin-shader'
evidence.mkdir(exist_ok=True)
log=(ROOT/'analysis/arch-gpu/wayland-smoke/f8-wayland-q1ivs7ng/weston.log').read_text()
lines=re.findall(r'^kwin_scene_opengl: line (\d+):(.*)$',log,re.M)
assert [int(n) for n,_ in lines]==list(range(1,len(lines)+1))
shader=evidence/'failed.frag';shader.write_text('\n'.join(text for _,text in lines)+'\n')
work=c.ssh('mktemp -d /tmp/f8-kwin-shader-XXXXXXXX',check=True,capture_output=True,text=True,timeout=30).stdout.strip()
assert re.fullmatch(r'/tmp/f8-kwin-shader-[A-Za-z0-9]{8}',work)
subprocess.run(['scp',*c.OPTIONS,str(shader),str(ROOT/'tools/probe-kwin-shader.py'),
                str(ROOT/'tools/probe-gpu-context.py'),c.HOST+':'+work+'/'],check=True,timeout=30)
result=c.ssh('env LD_LIBRARY_PATH=/opt/f8-pro/vendor-gpu-g13p0-20261028/lib timeout 20 python3 '+work+'/probe-kwin-shader.py',capture_output=True,text=True,timeout=30)
(evidence/'probe.log').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
subprocess.run(['scp',*c.OPTIONS,c.HOST+':'+work+'/result.json',str(evidence/'result.json')],check=True,timeout=30)
record=json.loads((evidence/'result.json').read_text());record['remote_work_directory']=work
(evidence/'result.json').write_text(json.dumps(record,indent=2)+'\n')
result.check_returncode()
