#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess,time
from pathlib import Path
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial').read_bytes()==b'c4\0'
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
folder=Path('/run/f8-camera-c4');folder.mkdir(exist_ok=True)
results={}
for name,node in [('front','/dev/video31'),('back','/dev/video22')]:
    target=folder/(name+'-640x480.nv12');assert not target.exists()
    cmd=['v4l2-ctl','-d',node,'--set-fmt-video=width=640,height=480,pixelformat=NV12',
         '--get-fmt-video','--stream-mmap=4','--stream-poll','--stream-count=8','--stream-to='+str(target)]
    started=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=12)
        result={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:
        result={'timeout':True,'stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')}
    result['seconds']=round(time.monotonic()-started,3)
    if target.exists():
        data=target.read_bytes()
        result.update(file=str(target),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                      expected_frame_bytes=640*480*3//2,frames_at_expected_size=len(data)/(640*480*3//2))
        if len(data)>=460800:
            y=data[-460800:-153600]
            result['last_frame_y']={'min':min(y),'max':max(y),'mean':sum(y)/len(y),'distinct_values':len(set(y))}
    results[name]=result
    dmesg=subprocess.check_output(['dmesg'],text=True)
    if result.get('exit')!=0 or any(s in dmesg for s in ['Internal error:','Kernel panic','Oops:']):break
    time.sleep(.5)
log=subprocess.check_output(['dmesg'],text=True)
health=subprocess.run(['systemctl','--failed','--no-pager'],capture_output=True,text=True)
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'results':results,
 'kernel_log_tail':'\n'.join(log.splitlines()[-160:]),'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),
 'failed_units':health.stdout},indent=2))
PY
