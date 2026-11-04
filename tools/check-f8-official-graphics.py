"""Compare F8 display bindings with the exact official DT and test CLI availability."""
from collections import Counter
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
E=P/'analysis/armbian/official-gpu-baseline-20261029'
O=P/'outputs/armbian/official-f8-graphics-r1b'
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
candidate=fdt((O/'f8-official-graphics-r1.NOT-APPROVED.dtb').read_bytes())
reference=fdt((root/'boot/dtb-6.1.115-vendor-rk35xx/rockchip/rk3588s-tablet-rk806-single-v10.dtb').read_bytes())
def cells(data):return list(struct.unpack('>'+str(len(data)//4)+'I',data))
def norm(tree,data,kind):
    handles={cells(p['phandle'])[0]:n for n,p in tree.items() if 'phandle' in p}
    values=cells(data);out=[];index=0
    while index<len(values):
        path=handles[values[index]];count=cells(tree[path][kind])[0]
        out.append([path,values[index+1:index+count+1]]);index+=count+1
    return out
rows=[]
for path in ['/vop@fdd90000','/iommu@fdd97e00','/dsi@fde20000','/phy@feda0000','/pwm@febf0020']:
    for key in ['compatible','reg','interrupts','interrupt-names','clock-names','clocks','phys','power-domains','iommus']:
        a=candidate[path].get(key);b=reference[path].get(key)
        if a is None and b is None:continue
        kind={'clocks':'#clock-cells','phys':'#phy-cells','power-domains':'#power-domain-cells','iommus':'#iommu-cells'}.get(key)
        aa=norm(candidate,a,kind) if kind and a else a
        bb=norm(reference,b,kind) if kind and b else b
        rows.append({'node':path,'property':key,'equal':aa==bb})
warnings=lambda text:Counter(re.findall(r'Warning \(([^)]+)\): ([^\n]+)',text))
baseline=(P/'outputs/armbian/firstboot-diagnostic-r5/diagnostic.dtc.log').read_text()
unexpected=list((warnings((O/'dtc.log').read_text())-warnings(baseline)).elements())
env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
help_result=subprocess.run(['chroot',str(root),'/usr/bin/kwin_wayland','--help'],env=env,capture_output=True,text=True,timeout=45)
(E/'kwin-cli-help.log').write_text(help_result.stdout+help_result.stderr)
supported={arg:arg in help_result.stdout for arg in ['--drm','--socket','--exit-with-session']}
report={'scope':'Offline display binding compatibility and actual ARM64 CLI checks, not hardware',
        'display_binding_checks':rows,'binding_differences':[r for r in rows if not r['equal']],
        'new_dtc_warnings':unexpected,'kwin_help_exit_code':help_result.returncode,
        'kwin_options_supported':supported,
        'wayland_cli_ready':help_result.returncode==0 and all(supported.values()),
        'hardware_test_performed':False}
(E/'graphics-binding-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert not unexpected
assert not report['binding_differences'], 'Review exact official binding differences before packaging'
assert report['wayland_cli_ready'], 'Adjust Wayland CLI to actual shipped KWin'
