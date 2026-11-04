"""Read USB2-only reference DTS settings and actual Image property strings."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
examples={}
for p in (S/'arch/arm64/boot/dts/rockchip').glob('rk3588*.dts*'):
    lines=p.read_text().splitlines()
    for i,line in enumerate(lines):
        if 'sel-pipe-phystatus' in line:examples[p.name+':'+str(i+1)]='\n'.join(lines[max(0,i-8):min(len(lines),i+9)])
kernel=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs/boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()
assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
core=(S/'drivers/usb/dwc3/core.c').read_text();lines=core.splitlines()
contexts='\n'.join('\n'.join(lines[max(0,i-4):min(len(lines),i+9)]) for i,line in enumerate(lines) if 'quirk-skip-phy-init' in line or 'skip_phy_initialization' in line)
result={'reference_commit':'85233a85b67928000afc2e966bab86a8c414f1b4','examples':examples,'property_string_present_in_actual_official_kernel':b'rockchip,sel-pipe-phystatus\0' in kernel,'core_skip_phy_context_reference':contexts}
out=P/'analysis/armbian/usb2-only-20261101.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
