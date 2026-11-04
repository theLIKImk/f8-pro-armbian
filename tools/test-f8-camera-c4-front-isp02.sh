#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
def run(args,timeout=10):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:return {'timeout':True,'stderr':(e.stderr or b'').decode(errors='replace')}
out={}
out['users']=run(['fuser','/dev/video0','/dev/video11','/dev/video22','/dev/video31'])
assert not out['users']['stdout'].strip(),out['users']
# Both defaults violate CIF's documented >=1000us ISP-online blanking warning.
# Modest line increases only; no exposure/gain or supply/register writes.
out['front_blanking']=run(['v4l2-ctl','-d','/dev/v4l-subdev2','--set-ctrl=vertical_blanking=80','--get-ctrl=vertical_blanking'])
out['back_blanking']=run(['v4l2-ctl','-d','/dev/v4l-subdev5','--set-ctrl=vertical_blanking=64','--get-ctrl=vertical_blanking'])
# v4l-utils 1.32 also issues the newer optional SUBDEV_S_CLIENT_CAP ioctl;
# this 6.1 kernel returns ENOTTY, making the CLI exit255 even when S/G_CTRL
# succeeded. Require the explicit readback instead of accepting exit alone.
for key,value in [('front_blanking',80),('back_blanking',64)]:
    assert out[key]['exit'] in (0,255) and f'vertical_blanking: {value}\n' in out[key]['stdout'],out
target=Path('/run/f8-camera-c4/front-isp02-640x480.nv12');assert not target.exists()
out['capture']=run(['v4l2-ctl','-d','/dev/video31','--set-fmt-video=width=640,height=480,pixelformat=NV12',
 '--get-fmt-video','--stream-mmap=4','--stream-poll','--stream-count=12','--stream-to='+str(target)],12)
data=target.read_bytes() if target.exists() else b''
out['bytes']=len(data);out['frames_at_640x480']=len(data)/460800
if len(data)>=460800:
    y=data[-460800:-153600]
    out['last_frame_y']={'min':min(y),'max':max(y),'mean':sum(y)/len(y)}
out['log_tail']=run(['sh','-c','dmesg | tail -65'])
print(json.dumps(out,indent=2))
PY
