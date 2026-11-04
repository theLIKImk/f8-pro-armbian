"""Check vendor plane assignments against pinned RK3588 VOP2 definitions."""
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'analysis/armbian/source-audit/linux-rockchip'
header = (ROOT / 'include/dt-bindings/display/rockchip_vop.h').read_text()
ids = {k: int(v) for k, v in re.findall(r'#define\s+(ROCKCHIP_VOP2_\w+)\s+(\d+)', header)}
names = {v: k for k, v in ids.items()}
source = (ROOT / 'drivers/gpu/drm/rockchip/rockchip_vop2_reg.c').read_text()
table = source.split('rk3588_vop_win_data[] = {', 1)[1].split('\n};', 1)[0]
windows = {}
for chunk in re.split(r'\n\t\{', table)[1:]:
    ident = re.search(r'\.phys_id\s*=\s*(\w+)', chunk)
    possible = re.search(r'\.possible_vp_mask\s*=\s*(.*?),', chunk, re.S)
    if ident and possible:
        windows.setdefault(ids[ident[1]], set()).update(int(x) for x in re.findall(r'ROCKCHIP_VOP_VP(\d)', possible[1]))
vendor = (BASE / 'analysis/baseline-validation/ubuntu-board.dts').read_text()
ports = vendor.split('\tvop@fdd90000 {', 1)[1].split('\tvop-opp-table', 1)[0]
records, union = [], 0
for vp, mask, primary in re.findall(r'port@(\d)\s*\{[^{}]*?rockchip,plane-mask = <(0x[0-9a-f]+)>;\s*rockchip,primary-plane = <(0x[0-9a-f]+)>;', ports):
    vp, mask, primary = int(vp), int(mask, 16), int(primary, 16)
    planes = [i for i in range(32) if mask & (1 << i)]
    assert mask & (1 << primary), 'Primary is outside mask'
    assert not union & mask, 'Plane assigned twice'
    for i in planes:
        assert vp in windows[i], (vp, i)
    union |= mask
    records.append({'vp': vp, 'mask': mask, 'primary': primary, 'planes': [names[i] for i in planes]})
assert len(records) == 4
assert union == sum(1 << i for i in windows), 'Not every physical window assigned'
out = BASE / 'analysis/armbian/vop-plane-audit.json'
out.write_text(json.dumps({'scope': 'Static driver capability checks, not runtime validation',
    'ports': records, 'all_windows_assigned_once': True,
    'possible_vps': {names[k]: sorted(v) for k, v in windows.items()}}, indent=2) + '\n')
text = '// SPDX-License-Identifier: GPL-2.0-only\n// Checked against pinned RK3588 VOP2 physical IDs; compile-check only.\n'
text += '#include <dt-bindings/display/rockchip_vop.h>\n'
for r in records:
    expression = ' | '.join('(1 << ' + name + ')' for name in r['planes'])
    text += f'\n&vp{r["vp"]} {{\n\trockchip,plane-mask = <({expression})>;\n\trockchip,primary-plane = <{names[r["primary"]]}>;\n}};\n'
text += '\n&vop {\n\tiommus = <&vop_mmu>;\n\tpower-domains = <&power RK3588_PD_VOP>;\n\tstatus = "disabled";\n};\n&vop_mmu { status = "disabled"; };\n'
(BASE / 'armbian/dts/f8-pro-vop.dtsi').write_text(text)
print(json.dumps(records))
