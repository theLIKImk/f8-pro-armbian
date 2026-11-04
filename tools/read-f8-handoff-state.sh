#!/bin/sh
# Read-only reconciliation after another agent's native-root changes.
set -eu
python3 -I - <<'PY'
import json, subprocess, hashlib
from pathlib import Path
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
paths=[
 '/usr/share/alsa/ucm2/F8-PRO/HiFi.conf',
 '/usr/share/alsa/ucm2/conf.d/rockchip_es8388/rockchip,es8388-codec.conf',
 '/usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf',
 '/usr/lib/systemd/system/f8-battery-cw2015.service',
 '/etc/modules-load.d/f8-cw2015.conf',
 '/etc/systemd/system/f8-usb-otg.service',
 '/usr/libexec/f8-pro/usb-otg-start.py',
 '/var/lib/alsa/asound.state']
files={}
for name in paths:
    p=Path(name)
    if p.is_file():
        data=p.read_bytes()
        files[name]={'sha256':hashlib.sha256(data).hexdigest(),'content':data.decode()}
    else:files[name]={'missing':True}
user=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601',
      'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
commands={
 'system': ['systemctl','is-system-running'],
 'failed':['systemctl','--failed','--no-legend','--no-pager'],
 'services':['systemctl','is-active','sddm','f8-usb-otg','f8-battery-cw2015','alsa-restore','upower'],
 'battery_service':['systemctl','show','f8-battery-cw2015','-p','ActiveState','-p','SubState','-p','ExecMainStatus','-p','ActiveEnterTimestampMonotonic'],
 'cpu_clocks':['sh','-c',"grep -E '(^| )((armclk|scmi_clk)[^ ]*) ' /sys/kernel/debug/clk/clk_summary || true"],
 'cpu_policies':['sh','-c','ls -d /sys/devices/system/cpu/cpufreq/policy* 2>/dev/null || true'],
 'default_sink':user+['pactl','get-default-sink'],
 'sources':user+['pactl','list','sources','short'],
 'sink_volume':user+['wpctl','get-volume','@DEFAULT_AUDIO_SINK@'],
 'battery':['sh','-c','for f in /sys/class/power_supply/cw2015-battery/{capacity,status,present}; do :; done; for n in capacity status present; do p=/sys/class/power_supply/cw2015-battery/$n; if [ -f "$p" ]; then echo "$n=$(cat "$p")"; fi; done'],
 'polkit_units':['systemctl','is-enabled','polkit-agent-helper.socket','polkit-agent-helper.service'],
 'polkit_helper_mode':['stat','-c','%a %U:%G %n','/usr/lib/polkit-1/polkit-agent-helper-1']}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'cmdline':Path('/proc/cmdline').read_text().strip(),'files':files,
 'checks':{k:run(v) for k,v in commands.items()}},ensure_ascii=False,indent=2))
PY
