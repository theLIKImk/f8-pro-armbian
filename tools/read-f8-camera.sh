#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=12)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
dt=Path('/sys/firmware/devicetree/base');nodes={}
for p in dt.rglob('*'):
    if p.is_dir() and (any(x in str(p.relative_to(dt)).lower() for x in ['gc5035','ov8858','rkisp','rkcif','csi2-dphy','csi2-dcphy','csi2@','mipi-camera']) or p.name=='i2c@fead0000'):
        nodes[str(p.relative_to(dt))]={q.name:q.read_bytes().hex() for q in p.iterdir() if q.is_file()}
commands={
 'config':['sh','-c',"grep -E '^CONFIG_(VIDEO_GC5035|VIDEO_OV8858|VIDEO_ROCKCHIP|VIDEO_RK|PHY_ROCKCHIP|MEDIA_CONTROLLER|VIDEO_V4L2_SUBDEV_API)' /boot/config-$(uname -r)"],
 'devices':['sh','-c','ls -l /dev/video* /dev/media* /dev/v4l-subdev* 2>/dev/null'],
 'list':['v4l2-ctl','--list-devices'],
 'media':['sh','-c','for m in /dev/media*; do test -e "$m" || continue; media-ctl -d "$m" -p; done'],
 'modules':['sh','-c',"lsmod | grep -Ei 'isp|cif|camera|ov8858|gc5035|mipi'; find /lib/modules/$(uname -r) -iname '*gc5035*' -o -iname '*ov8858*' -o -iname '*rkisp*' -o -iname '*rkcif*'"],
 'packages':['sh','-c',"dpkg-query -W '*rkaiq*' '*libcamera*' 'v4l-utils' 'gstreamer1.0-tools' 'gstreamer1.0-plugins-good' 'gstreamer1.0-plugins-bad' 'qcam' 2>/dev/null; command -v gst-launch-1.0; command -v cam; command -v qcam"],
 'logs':['sh','-c',"dmesg | grep -Ei 'gc5035|ov8858|rkisp|rkcif|csi2|camera|feac0000' | tail -90"],
 'i2c':['sh','-c','cat /sys/bus/i2c/devices/i2c-5/name; ls -l /sys/bus/i2c/devices/5-* 2>/dev/null'],
 'iqfiles':['sh','-c',"find /etc/iqfiles /usr/share/iqfiles /usr/share/rkaiq /usr/lib -maxdepth 3 -iname '*gc5035*' -o -iname '*ov8858*' -o -iname '*rkaiq*' 2>/dev/null | head -35"],
 'pins':['sh','-c',"grep -E 'feac0000|camera|cif|mipi|clkout' /sys/kernel/debug/pinctrl/*/pinmux-pins"],
 'regulators':['cat','/sys/kernel/debug/regulator/regulator_summary']}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'nodes':nodes,'checks':{k:run(v) for k,v in commands.items()}},indent=2))
PY
