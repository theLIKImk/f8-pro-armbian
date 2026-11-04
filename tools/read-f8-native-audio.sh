#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess,re
from pathlib import Path
base=Path('/sys/firmware/devicetree/base')
nodes={}
for p in base.rglob('compatible'):
    raw=p.read_bytes()
    if b'es83' in raw or b'multicodecs' in raw or b'rk3588-i2s' in raw:
        data={}
        for name in ['compatible','status','reg','clock-names','rockchip,card-name','rockchip,audio-routing','spk-con-gpios','pinctrl-0']:
            f=p.parent/name
            if f.is_file():data[name]=f.read_bytes().hex()
        nodes['/'+str(p.parent.relative_to(base))]=data
mods=[str(p.relative_to('/lib/modules')) for p in Path('/lib/modules').rglob('*') if p.is_file() and any(x in p.name.lower() for x in ['es83','multicodec','rockchip_i2s','rockchip-i2s'])]
config=Path('/boot/config-6.1.115-vendor-rk35xx')
cfg=[]
if config.exists():cfg=[s for s in config.read_text().splitlines() if 'SND_SOC' in s and any(x in s for x in ['ES83','ROCKCHIP_I2S','MULTICODEC'])]
claims={}
for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'):
    lines=[s for s in p.read_text().splitlines() if re.search(r'^pin (50|51|53|55|56|57|60|130|133) \(',s)]
    if lines:claims[str(p)]=lines
print(json.dumps({'audio_dt':nodes,'module_files':mods,'config':cfg,'pinmux_claims':claims,'i2c_adapters':{p.name:(p/'name').read_text().strip() for p in Path('/sys/class/i2c-adapter').glob('*')}},indent=2))
PY
