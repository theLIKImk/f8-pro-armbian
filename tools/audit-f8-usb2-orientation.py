import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
out=P/'analysis/armbian/usb2-orientation-20261101';out.mkdir(exist_ok=True)
source=S/'drivers/phy/rockchip/phy-rockchip-inno-usb2.c';text=source.read_text()
keys=['rockchip_usb2phy_usb_bvalid_enable','rockchip_usb2phy_orien_sw_set','rockchip_usb2phy_setup_orien_switch']
contexts={}
for key in keys:
    match=re.search(r'static\s+(?:int|void)\s+'+key+r'\s*\(',text)
    assert match,key
    start=match.start();brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    contexts[key]=text[start:end]
examples={}
for p in (S/'arch/arm64/boot/dts/rockchip').glob('rk3588*.dts*'):
    lines=p.read_text().splitlines()
    for i,line in enumerate(lines):
        if 'orientation-switch' in line:
            snippet='\n'.join(lines[max(0,i-5):min(len(lines),i+10)])
            if 'u2phy' in snippet:examples[p.name+':'+str(i+1)]=snippet
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reference_only':True,'contexts':contexts,'usb2phy_orientation_examples':examples}
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
