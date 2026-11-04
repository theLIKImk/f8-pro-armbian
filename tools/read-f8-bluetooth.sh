#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
base=Path('/sys/firmware/devicetree/base');nodes={}
for p in base.rglob('compatible'):
    if b'bluetooth' in p.read_bytes() or p.parent.name in ['serial@febc0000','hym8563@51']:
        nodes[str(p.parent.relative_to(base))]={q.name:q.read_bytes().hex() for q in p.parent.iterdir() if q.is_file()}
cmds={
 'rfkill':['rfkill','list'], 'hci':['bluetoothctl','list'],
 'services':['systemctl','status','bluetooth','f8-bluetooth','--no-pager','-l'],
 'uarts':['sh','-c','ls -l /dev/ttyS*; cat /proc/tty/driver/serial'],
 'modules':['sh','-c',"lsmod | grep -E 'bluetooth|hci|bcm|rfkill'; modinfo hci_uart | head -25"],
 'config':['sh','-c',"grep -E 'CONFIG_(BT|RFKILL|RTC_DRV_HYM8563)' /boot/config-$(uname -r)"],
 'logs':['sh','-c',"dmesg | grep -Ei 'bluetooth|hci|rfkill|uart9|ttyS9|hym8563'"],
 'gpio':['cat','/sys/kernel/debug/gpio'],
 'assets':['sh','-c',"find /vendor /usr/lib/firmware /usr/libexec/f8-pro -iname '*4362*' -o -iname '*patchram*' -o -iname '*bluetooth*' 2>/dev/null"],
 'processes':['sh','-c',"ps -eo pid,comm,args | grep -E 'patchram|hciattach|btattach|bluetoothd' | grep -v grep"],
 'uart9_pins':['sh','-c',"grep -E 'pin (28|22|21|122|123|124|125) ' /sys/kernel/debug/pinctrl/*/pinmux-pins 2>/dev/null"]}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'nodes':nodes,'checks':{k:run(v) for k,v in cmds.items()}},indent=2))
PY
