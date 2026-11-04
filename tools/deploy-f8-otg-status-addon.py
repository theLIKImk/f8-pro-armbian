"""Load a RAM-only passive status addon without replacing the OTG control driver."""
import base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];base=P/'outputs/armbian/official-f8-usb-u1-module-passive-addon'
meta=json.loads((base/'module-check.json').read_text());assert meta['all_import_crcs_match_actual_official_kernel']
blob=(base/meta['module']).read_bytes();assert hashlib.sha256(blob).hexdigest()==meta['sha256']
dest=P/'local/hardware/armbian-native-usb-20261101/u4r1';out=dest/'status-addon01.json';runner=dest/'status-addon01-runner.sh'
assert not out.exists() and not runner.exists()
code='''import base64,hashlib,json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='d83ba29d-2d56-4a09-8240-2bee4bf10466'
assert not Path('/sys/class/typec/port0-partner').exists()
assert Path('/sys/module/f8_otg_vbus').exists() and not Path('/sys/module/f8_otg_status').exists()
assert Path('/sys/bus/i2c/devices/6-0022/driver').resolve().name=='typec_fusb302'
assert Path('/sys/bus/i2c/devices/6-006a/driver').resolve().name=='f8-otg-vbus'
directory=Path('/run/f8/passive-usb-status01');directory.mkdir(exist_ok=False)
module=directory/'f8_otg_status.ko';data=base64.b64decode(PAYLOAD)
assert hashlib.sha256(data).hexdigest()==DIGEST;module.write_bytes(data);module.chmod(0o600)
r=subprocess.run(['insmod',str(module)],capture_output=True,text=True,timeout=15)
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'module_sha256':DIGEST,'load_exit':r.returncode,'stderr':r.stderr,'original_control_driver_replaced':False,'register_configuration_writes':False,'module_ram_only':True}
if r.returncode==0:result['unplugged_status']=Path('/sys/bus/i2c/devices/6-006a/f8_usb_status/status').read_text().strip()
print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(base64.b64encode(blob).decode())).replace('DIGEST',repr(meta['sha256']))
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1600:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
