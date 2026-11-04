#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess,re
from pathlib import Path
def read(p):
    try:return p.read_text().strip()
    except OSError:return None
def cmd(args):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
def attrs(p,names):return {n:read(p/n) for n in names if (p/n).exists()}
dt=Path('/sys/firmware/devicetree/base')
nodes={}
for p in dt.rglob('*'):
    if p.is_dir() and re.search(r'usb|typec|fusb|vbus|tcphy|usbdp',p.name,re.I):
        props={}
        for name in ['compatible','status','dr_mode','maximum-speed','role-switch-default-mode','usb-role-switch','extcon','vbus-supply','phys','phy-names','data-role','power-role','try-power-role']:
            f=p/name
            if f.exists():
                b=f.read_bytes();props[name]=b.rstrip(b'\0').decode('ascii') if all(x==0 or 32<=x<127 for x in b) else b.hex()
        if props:nodes[str(p.relative_to(dt))]=props
usb={p.name:attrs(p,['idVendor','idProduct','manufacturer','product','bDeviceClass','speed','authorized','busnum','devnum']) for p in Path('/sys/bus/usb/devices').glob('*') if (p/'idVendor').exists()}
roles={str(p):read(p/'role') for p in Path('/sys/class/usb_role').glob('*')}
typec={p.name:attrs(p,['data_role','power_role','port_type','power_operation_mode','preferred_role','accessory_mode','supports_usb_power_delivery']) for p in Path('/sys/class/typec').glob('*')}
udc={p.name:attrs(p,['state','current_speed','maximum_speed','is_otg','function']) for p in Path('/sys/class/udc').glob('*')}
gadget={p.name:{'UDC':read(p/'UDC'),'functions':[q.name for q in (p/'functions').glob('*')]} for p in Path('/sys/kernel/config/usb_gadget').glob('*')}
platform={p.name:str((p/'driver').resolve()) if (p/'driver').is_symlink() else None for p in Path('/sys/bus/platform/devices').glob('*') if re.search(r'usb|dwc|xhci|ehci|ohci|typec|usbdp',p.name,re.I)}
log=cmd(['dmesg']);log['stdout']='\n'.join(s for s in log.get('stdout','').splitlines() if re.search(r'usb|dwc|xhci|ehci|ohci|typec|fusb|extcon|vbus|tcpm',s,re.I))[-22000:]
print(json.dumps({'boot_id':read(Path('/proc/sys/kernel/random/boot_id')),'usb_devices':usb,'roles':roles,'typec':typec,'udc':udc,'gadgets':gadget,'platform_drivers':platform,'dt':nodes,'lsusb':cmd(['lsusb','-t']),'deferred':cmd(['cat','/sys/kernel/debug/devices_deferred']),'usb_log':log,'scope':'Read-only USB diagnosis; no role, regulator, PD or battery writes'},indent=2))
PY
