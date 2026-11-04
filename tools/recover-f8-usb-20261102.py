"""Recover a failed U5 probe after the user explicitly emptied the USB-C port.
Only clear the existing OTG_CONFIG bit; never change charger/boost policy.
"""
import ctypes,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/sys/firmware/devicetree/base/chosen/f8-usb-trial').read_bytes()==b'u5\0'
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')
assert hashlib.sha256(module.read_bytes()).hexdigest()=='a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c'
assert not Path('/sys/bus/i2c/devices/6-006a/driver').is_symlink(),'Already bound; do not touch charger through i2c-dev'
assert not list(Path('/sys/class/typec').glob('*partner*'))
assert not [p for p in Path('/sys/bus/usb/devices').glob('*') if (p/'idVendor').exists()]
assert Path('/sys/module/f8_otg_vbus').exists()
class Data(ctypes.Union):_fields_=[('byte',ctypes.c_ubyte),('block',ctypes.c_ubyte*34)]
class Request(ctypes.Structure):_fields_=[('read_write',ctypes.c_ubyte),('command',ctypes.c_ubyte),('size',ctypes.c_uint32),('data',ctypes.POINTER(Data))]
fd=os.open('/dev/i2c-6',os.O_RDWR|os.O_CLOEXEC)
def access(reg,value=None):
 d=Data()
 if value is not None:d.byte=value
 r=Request(1 if value is None else 0,reg,2,ctypes.pointer(d));fcntl.ioctl(fd,0x0720,r);return int(d.byte)
audit={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'user_confirmed_port_empty':True,'started':time.time(),'writes':[]}
folder=Path('/var/lib/f8-pro/usb-recovery-20261102');folder.mkdir(exist_ok=True,parents=True);folder.chmod(0o700)
def save():
 p=folder/'runtime-recovery.json';p.write_text(json.dumps(audit,indent=2)+'\n');p.chmod(0o600)
try:
 fcntl.ioctl(fd,0x0703,0x6a)
 before={f'{reg:02x}':access(reg) for reg in [3,7,10,11,20]};audit['before']=before;save()
 assert ((before['14']>>3)&7)==3,'Unexpected charger identity'
 assert not before['07']&0x30,'Watchdog is enabled; no policy change allowed'
 assert not before['03']&0x40,'Watchdog-reset strobe present'
 assert ((before['0b']>>5)&7) in [0,7],'Detected incoming source'
 if before['03']&0x20:
  value=before['03']&~0x20
  access(3,value);audit['writes'].append({'register':'03','old':before['03'],'new':value,'mask':32});save()
  assert access(3)==value,'OTG clear readback mismatch'
  time.sleep(.7)
 after={f'{reg:02x}':access(reg) for reg in [3,7,10,11,20]};audit['after']=after
 assert after['03']==before['03']&~0x20
 assert after['07']==before['07'] and after['0a']==before['0a']
 save()
finally:os.close(fd)
# Normal driver probe now owns GPIO and regulator policy; do not force USB host role.
Path('/sys/bus/i2c/drivers/f8-otg-vbus/bind').write_text('6-006a')
time.sleep(1)
if not Path('/sys/bus/i2c/devices/6-0022/driver').is_symlink():Path('/sys/bus/i2c/drivers_probe').write_text('6-0022')
r=subprocess.run(['systemctl','restart','f8-usb-otg.service'],capture_output=True,text=True,timeout=18)
audit['service_restart']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
audit['bindings']={n:(Path('/sys/bus/i2c/devices')/n/'driver').resolve().name for n in ['6-006a','6-0022']}
audit['typec']={p.name:{k:(p/k).read_text().strip() for k in ['data_role','power_role'] if (p/k).exists()} for p in Path('/sys/class/typec').glob('port[0-9]')}
audit['usb_devices']=[p.name for p in Path('/sys/bus/usb/devices').glob('*')]
save();print(json.dumps(audit,indent=2))
assert r.returncode==0 and audit['bindings']=={'6-006a':'f8-otg-vbus','6-0022':'typec_fusb302'}
assert audit['typec'], 'Type-C class missing after probe'
# Empty dual-role port may remain device/sink with no USB host root hub.
# Peripheral enumeration is tested separately after the user inserts a drive.
