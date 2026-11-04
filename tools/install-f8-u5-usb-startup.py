"""Install a late, version-guarded USB service on the native writable root."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-usb-20261101/u5'
out=dest/'startup-install01.json';runner=dest/'startup-install01-runner.sh';assert not out.exists() and not runner.exists()
sources={ '/usr/libexec/f8-pro/usb-otg-start.py':(P/'armbian/usb/usb-otg-start.py').read_bytes(), '/etc/systemd/system/f8-usb-otg.service':(P/'armbian/usb/f8-usb-otg.service').read_bytes() }
payload={name:base64.b64encode(data).decode() for name,data in sources.items()}
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='9df01d2b-d624-4364-8d3d-a06ff6847720'
assert Path('/sys/firmware/devicetree/base/chosen/f8-usb-trial').read_bytes()==b'u5\\0'
assert not Path('/sys/class/typec/port0-partner').exists(),'Tablet USB port must be empty'
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
stage=Path('/var/lib/f8-pro/usb-u5-startup01');stage.mkdir(exist_ok=False)
created=[];result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def cmd(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=25)
    assert r.returncode==0,(args,r.stderr[-1500:])
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
try:
    for name,data in payload.items():
        body=base64.b64decode(data)
        if name.endswith('.py'):compile(body,name,'exec')
        path=Path(name);path.write_bytes(body);path.chmod(0o644);created.append(path)
    result['verify']=cmd(['systemd-analyze','verify','/etc/systemd/system/f8-usb-otg.service'])
    result['reload']=cmd(['systemctl','daemon-reload'])
    result['enable']=cmd(['systemctl','enable','f8-usb-otg.service'])
    result['start']=cmd(['systemctl','start','f8-usb-otg.service'])
    result['service']=cmd(['systemctl','show','f8-usb-otg.service','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus'])
    assert 'ActiveState=active' in result['service']['stdout'] and 'Result=success' in result['service']['stdout']
    result['files_sha256']={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in payload}
    result['success']=True
except Exception as error:
    result['error']=str(error)
    subprocess.run(['systemctl','disable','--now','f8-usb-otg.service'],capture_output=True,timeout=15)
    for path in created:path.unlink()
    subprocess.run(['systemctl','daemon-reload'],capture_output=True,timeout=15)
    result['success']=False
(stage/'result.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(payload))
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1600:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
