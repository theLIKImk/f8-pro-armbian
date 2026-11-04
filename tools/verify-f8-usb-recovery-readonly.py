import json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/sys/bus/usb/devices/1-1');assert (p/'idVendor').read_text().strip()=='152d' and (p/'idProduct').read_text().strip()=='0583'
assert '[host]' in Path('/sys/class/typec/port0/data_role').read_text()
assert '[source]' in Path('/sys/class/typec/port0/power_role').read_text()
sys=Path('/sys/class/block/sda');assert str(sys.resolve()).startswith(str(p.resolve())+'/')
f=os.open('/dev/sda',os.O_RDONLY|os.O_CLOEXEC)
try:count=len(os.pread(f,4096,0));assert count==4096
finally:os.close(f)
o={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'time':time.time(),'block_read_bytes':count,'capacity_bytes':int((sys/'size').read_text())*512,'speed_mbps':int((p/'speed').read_text()),'agent_disk_write_test_performed':False}
o['failed_units']=subprocess.check_output(['systemctl','--failed','--no-legend','--no-pager'],text=True)
o['mounts']=[{'source':s[0],'filesystem':s[2],'options':s[3]} for l in Path('/proc/mounts').read_text().splitlines() if (s:=l.split())[0] in ['/dev/sda1','/dev/sda2']]
print(json.dumps(o,indent=2))
