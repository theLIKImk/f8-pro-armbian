#!/usr/bin/python3
"""Guard the BT1 board profile, then attach the verified factory UART firmware."""
import hashlib,os,re,subprocess
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
assert (dt/'chosen/f8-bluetooth-trial').read_bytes()==b'bt1\0'
assert (dt/'aliases/serial9').read_bytes()==b'/serial@febc0000\0'
for node in ['serial@febc0000','wireless-bluetooth','i2c@fec80000/hym8563@51']:
    assert (dt/node/'status').read_bytes()==b'okay\0'
assert Path('/sys/bus/platform/devices/wireless-bluetooth/driver').exists(),'rfkill platform driver not bound'
helper='/usr/libexec/f8-pro/brcm_patchram_plus1'
firmware='/usr/lib/firmware/f8-pro/BCM4362A2.hcd'
for name,digest in [(helper,'f69ba38d29d7745e88df7cfec6314a1704929dfbaf029fdd8f9c4f140e907d03'),
                    (firmware,'18901a5bef1d418b6895e92d0afae36234f4160b237465dfca3d75e9844e93ef')]:
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
assert not list(Path('/sys/class/bluetooth').glob('hci*')),'Another controller attachment is already active'
machine_id=Path('/etc/machine-id').read_text().strip().lower()
assert re.fullmatch('[0-9a-f]{32}',machine_id) and machine_id!='0'*32
value=bytearray(hashlib.sha256(b'f8-pro-bluetooth\0'+machine_id.encode()).digest()[:6]);value[0]=(value[0]|2)&254
mac=':'.join(f'{n:02X}' for n in value)
subprocess.run(['modprobe','hci_uart'],check=True,timeout=15)
subprocess.run(['rfkill','unblock','bluetooth'],check=True,timeout=10)
print('BT1: attaching factory BCM4362 firmware on UART9',flush=True)
os.execv(helper,[helper,'--bd_addr',mac,'--enable_hci','--no2bytes','--use_baudrate_for_download',
 '--tosleep','200000','--baudrate','1500000','--patchram',firmware,'/dev/ttyS9'])
