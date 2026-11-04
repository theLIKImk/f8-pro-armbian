"""Verify U2 before loading its OTG driver; preserve independent evidence."""
import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-usb-20261101/u2';dest.mkdir(exist_ok=True)
def capture(name,script):
    out=dest/(name+'.json');assert not out.exists(),'Preserve evidence'
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(script),'--sudo'],capture_output=True,text=True,timeout=100)
    assert r.returncode==0,r.stderr[-1600:]
    d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');return d
runner=dest/'identity-runner.sh'
runner.write_text('''#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
cmdline=Path('/proc/cmdline').read_text().strip()
assert 'f8_usb_u1=1' in cmdline and 'systemd.gpt_auto=0' in cmdline
assert (dt/'i2c@fec80000/charger@6a/compatible').read_bytes()==b'f8-pro,otg-vbus-only\\0'
assert (dt/'usbdrd3_0/usb@fc000000/dr_mode').read_bytes()==b'otg\\0'
assert not Path('/sys/module/f8_otg_vbus').exists(),'Expected staged-only module'
module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')
digest=hashlib.sha256(module.read_bytes()).hexdigest()
assert digest=='a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c'
power=subprocess.check_output(['systemctl','show','f8-live-power.service','-p','ActiveState','-p','SubState','-p','ConditionResult'],text=True)
assert 'ActiveState=inactive' in power and 'ConditionResult=no' in power,power
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'model':(dt/'model').read_bytes().rstrip(b'\\0').decode(),'cmdline':cmdline,'module_staged_hash':digest,'module_loaded':False,'power_service':power,'kernel':subprocess.check_output(['uname','-r'],text=True).strip()},indent=2))
PY
''')
d=capture('identity',runner);print(json.dumps({'identity':d}),flush=True)
desktop=dest/'desktop-runner.sh'
text=(P/'tools/verify-f8-native-desktop.sh').read_text()
assert text.count(",'f8-live-power'")==1
desktop.write_text(text.replace(",'f8-live-power'",''))
d=capture('desktop',desktop);print(json.dumps({'desktop':d}),flush=True)
d=capture('backlight',P/'tools/read-f8-backlight-ownership.sh');print(json.dumps({'backlight':d}),flush=True)
d=capture('usb-before-module',P/'tools/read-f8-usb-runtime.sh');print(json.dumps({'usb':{k:d.get(k) for k in ['boot_id','roles','typec','usb_devices','deferred','usb_log']}}),flush=True)
