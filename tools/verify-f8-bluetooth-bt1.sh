#!/bin/sh
# Read-only verification. Do not scan, pair, record audio or change radio state.
set -eu
python3 -I - <<'PY'
import json,re,subprocess
from pathlib import Path
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
dt=Path('/sys/firmware/devicetree/base')
assert (dt/'chosen/f8-bluetooth-trial').read_bytes()==b'bt1\0'
assert (dt/'chosen/f8-usb-trial').read_bytes()==b'u5\0'
assert Path('/dev/ttyS9').exists()
assert Path('/sys/bus/platform/devices/wireless-bluetooth/driver').exists()
assert Path('/sys/bus/i2c/devices/6-0051/driver').exists()
hci=[p for p in Path('/sys/class/bluetooth').glob('hci*') if re.fullmatch(r'hci[0-9]+',p.name)];assert len(hci)==1,[p.name for p in hci]
services=run(['systemctl','is-active','f8-bluetooth','bluetooth','f8-usb-otg','sddm'])
assert services['exit']==0,services
controller=run(['bluetoothctl','show']);assert controller['exit']==0 and 'Powered: yes' in controller['stdout'],controller
failed=run(['systemctl','--failed','--no-legend','--no-pager']);assert failed['exit']==0 and not failed['stdout'].strip(),failed
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'verified':True,'hci_count':len(hci),'services':services,'controller':controller,'failed_units':failed,
 'enabled':run(['systemctl','is-enabled','f8-bluetooth']),
 'clock':run(['sh','-c',"grep -i hym8563 /sys/kernel/debug/clk/clk_summary"]),
 'service_boot':run(['systemctl','show','f8-bluetooth','-p','ActiveEnterTimestampMonotonic','-p','ExecMainStartTimestampMonotonic','-p','NRestarts','-p','ExecMainStatus']),
 'kernel_version':run(['uname','-r'])},indent=2))
PY
