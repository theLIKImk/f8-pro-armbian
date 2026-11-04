"""Read-only USB health snapshot; no role switching, mount, reset, or device writes."""
import json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
out={'timestamp':time.time(),'read_only_check':True}
def read(p):
 try:return Path(p).read_text().strip()
 except (OSError,UnicodeError):return None
def run(a):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
out['boot_id']=read('/proc/sys/kernel/random/boot_id');out['kernel']=run(['uname','-r'])
out['profile']=read('/sys/firmware/devicetree/base/chosen/f8-usb-trial')
out['services']=run(['systemctl','show','f8-usb-otg.service','udisks2.service','-p','Id','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus'])
out['startup_log']=run(['journalctl','-b','-u','f8-usb-otg.service','--no-pager','-n','25'])
out['typec']={p.name:{k:read(p/k) for k in ['data_role','power_role','port_type','power_operation_mode','orientation','accessory_mode','usb_power_delivery_revision']} for p in Path('/sys/class/typec').glob('*')}
out['usb']={}
for p in sorted(Path('/sys/bus/usb/devices').glob('*')):
 d={k:read(p/k) for k in ['idVendor','idProduct','product','manufacturer','speed','authorized','bDeviceClass','bInterfaceClass','busnum','devnum','power/runtime_status']};d={k:v for k,v in d.items() if v is not None}
 if (p/'driver').is_symlink():d['driver']=(p/'driver').resolve().name
 out['usb'][p.name]=d
out['roles']={p.name:read(p/'role') for p in Path('/sys/class/usb_role').glob('*')}
out['bindings']={name:((Path('/sys/bus/i2c/devices')/name/'driver').resolve().name if (Path('/sys/bus/i2c/devices')/name/'driver').is_symlink() else None) for name in ['6-0022','6-006a']}
out['module_present']=Path('/sys/module/f8_otg_vbus').exists()
out['module_parameters']={p.name:read(p) for p in Path('/sys/module/f8_otg_vbus/parameters').glob('*')}
out['usb_blocks']={}
for p in Path('/sys/class/block').glob('*'):
 if '/usb' in str(p.resolve()):out['usb_blocks'][p.name]={'sectors':read(p/'size'),'partition':read(p/'partition'),'read_only':read(p/'ro')}
out['usb_mounts']=[]
for line in Path('/proc/mounts').read_text().splitlines():
 s=line.split()
 if s[0] in ['/dev/'+x for x in out['usb_blocks']]:out['usb_mounts'].append({'device':s[0],'filesystem':s[2],'options':s[3]})
out['usb_log']=run(['journalctl','-k','-b','--no-pager','--grep','usb |usb-storage|xhci|dwc3|fusb|typec|otg|uas|I/O error|over.current','-n','100'])
print(json.dumps(out,indent=2))
