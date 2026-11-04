#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,signal,subprocess,time
from pathlib import Path
raise SystemExit('Disabled: generic multi-camera AIQ crashed with ISP21 front IQ on ISP30. Use a validated per-camera harness; do not start this server.')
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')
assert not (folder/'aiq-trial.log').exists()
out={};log=folder/'aiq-trial.log'
env={**os.environ,'LD_LIBRARY_PATH':str(root/'lib')}
with log.open('w') as output:
    server=subprocess.Popen([str(root/'bin/rkaiq_3A_server')],stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
    try:
        time.sleep(2)
        out['server_after_2s']=server.poll()
        if server.poll() is None:
            for name,node in [('front','/dev/video31'),('back','/dev/video22')]:
                target=folder/(name+'-aiq-640x480.nv12');assert not target.exists()
                try:
                    p=subprocess.run(['v4l2-ctl','-d',node,'--set-fmt-video=width=640,height=480,pixelformat=NV12',
                      '--stream-mmap=4','--stream-poll','--stream-count=30','--stream-to='+str(target)],capture_output=True,text=True,timeout=10)
                    result={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
                except subprocess.TimeoutExpired as e:
                    result={'timeout':True,'stderr':(e.stderr or b'').decode(errors='replace')}
                data=target.read_bytes() if target.exists() else b''
                result.update(bytes=len(data),frames=len(data)/460800)
                if len(data)>=460800:
                    y=data[-460800:-153600]
                    result['last_frame_y']={'min':min(y),'max':max(y),'mean':sum(y)/len(y)}
                out[name]=result
                time.sleep(.5)
    finally:
        if server.poll() is None:
            os.killpg(server.pid,signal.SIGTERM)
            try:server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid,signal.SIGKILL);server.wait(timeout=3)
        out['server_exit']=server.returncode
out['server_log']=log.read_text(errors='replace')[-22000:]
out['kernel_log_tail']=subprocess.check_output(['dmesg'],text=True).splitlines()[-90:]
out['server_left_running']=False
print(json.dumps(out,indent=2))
PY
