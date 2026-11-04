"""Disassemble only selected USB PHY functions from the actual official Image."""
import hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
image=root/'boot/vmlinuz-6.1.115-vendor-rk35xx';data=image.read_bytes()
assert hashlib.sha256(data).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
symbols=[]
for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines():
    fields=line.split()
    if len(fields)==3:symbols.append((int(fields[0],16),fields[1],fields[2]))
lookup={n:(a,k) for a,k,n in symbols};base=lookup['_text'][0]
out=P/'analysis/armbian/official-usb-phy-20261101';out.mkdir(exist_ok=True)
selected=['rockchip_usb2phy_set_mode','rockchip_usb2phy_otg_port_init','rockchip_usb2phy_orien_sw_set','otg_mode_store','dwc3_usb_role_switch_set']
report={}
for name in selected:
    if name not in lookup:continue
    address,kind=lookup[name];end=min(a for a,k,n in symbols if a>address and k.lower()=='t')
    assert 0<end-address<20000
    target=out/(name+'.asm')
    r=subprocess.run(['aarch64-linux-gnu-objdump','-D','-b','binary','-m','aarch64','--adjust-vma='+hex(base),'--start-address='+hex(address),'--stop-address='+hex(end),str(image)],capture_output=True,text=True,check=True)
    target.write_text(r.stdout);report[name]={'address':hex(address),'bytes':end-address,'assembly_file':str(target.relative_to(P))}
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx/include/linux/phy/phy.h')
text=H.read_text();start=text.index('enum phy_mode');end=text.index('};',start)+2
(out/'official-header-phy-mode.txt').write_text(text[start:end]+'\n')
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
