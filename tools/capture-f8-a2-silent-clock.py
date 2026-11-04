import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-native-audio-a2-20261030-01/silent-clock-01.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/probe-f8-a2-silent-clock.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1200:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/sound/soc/rockchip/rockchip_i2s_tdm.c')
if source.exists():
    lines=source.read_text().splitlines();picked=set()
    for i,line in enumerate(lines):
        if any(s in line for s in ['pinctrl_select_state','pinctrl_lookup_state']):picked.update(range(max(0,i-4),min(len(lines),i+5)))
    (out.parent/'reference-i2s-pinctrl-context.txt').write_text('\n'.join(str(i+1)+': '+lines[i] for i in sorted(picked))+'\n')
