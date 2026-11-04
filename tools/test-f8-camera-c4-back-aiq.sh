#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,signal,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')
# Exact factory back IQ is ISP30. Front file is ISP21: explicitly never load it
# into this ISP30 library. Keep both original files unmodified for provenance.
iq=json.loads((root/'iqfiles/ov8858_HS5885-BNSM1018-V01_default.json').read_text())
assert 'scene_isp30' in iq['main_scene'][0]['sub_scene'][0]
child=r'''
import ctypes as C,signal,sys,time
lib=C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so')
lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd.argtypes=[C.c_char_p]
lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd.restype=C.c_char_p
name=lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd(b'/dev/video22')
print('SENSOR',name,flush=True);assert name==b'm00_b_ov8858 5-0036'
lib.rk_aiq_uapi2_sysctl_preInit_scene.argtypes=[C.c_char_p,C.c_char_p,C.c_char_p]
lib.rk_aiq_uapi2_sysctl_preInit_scene.restype=C.c_int
print('SCENE',lib.rk_aiq_uapi2_sysctl_preInit_scene(name,b'normal',b'day'),flush=True)
lib.rk_aiq_uapi2_sysctl_init.argtypes=[C.c_char_p,C.c_char_p,C.c_void_p,C.c_void_p]
lib.rk_aiq_uapi2_sysctl_init.restype=C.c_void_p
ctx=lib.rk_aiq_uapi2_sysctl_init(name,b'/opt/f8-pro-camera/aiq-v6-c4/iqfiles',None,None)
print('INIT',bool(ctx),flush=True);assert ctx
lib.rk_aiq_uapi2_sysctl_prepare.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_int]
lib.rk_aiq_uapi2_sysctl_prepare.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_start.argtypes=[C.c_void_p];lib.rk_aiq_uapi2_sysctl_start.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_stop.argtypes=[C.c_void_p,C.c_bool];lib.rk_aiq_uapi2_sysctl_stop.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_deinit.argtypes=[C.c_void_p];lib.rk_aiq_uapi2_sysctl_deinit.restype=None
signal.signal(signal.SIGTERM,lambda *a:sys.exit(0))
try:
    result=lib.rk_aiq_uapi2_sysctl_prepare(ctx,3264,2448,0);print('PREPARE',result,flush=True);assert result==0
    result=lib.rk_aiq_uapi2_sysctl_start(ctx);print('AIQ_READY',result,flush=True);assert result==0
    time.sleep(18)
finally:
    print('STOP',lib.rk_aiq_uapi2_sysctl_stop(ctx,False),flush=True)
    lib.rk_aiq_uapi2_sysctl_deinit(ctx)
'''
log=folder/'back-aiq-trial.log';assert not log.exists()
out={}
with log.open('w') as output:
    server=subprocess.Popen(['python3','-u','-c',child],stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        for _ in range(40):
            if server.poll() is not None or 'AIQ_READY 0' in log.read_text(errors='replace'):break
            time.sleep(.1)
        out['server_before_capture']=server.poll()
        if server.poll() is None and 'AIQ_READY 0' in log.read_text(errors='replace'):
            target=folder/'back-aiq02-640x480.nv12';assert not target.exists()
            try:
                p=subprocess.run(['v4l2-ctl','-d','/dev/video22','--set-fmt-video=width=640,height=480,pixelformat=NV12',
                  '--stream-mmap=4','--stream-poll','--stream-count=45','--stream-to='+str(target)],capture_output=True,text=True,timeout=10)
                out['capture']={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
            except subprocess.TimeoutExpired as e:out['capture']={'timeout':True,'stderr':(e.stderr or b'').decode(errors='replace')}
            data=target.read_bytes() if target.exists() else b''
            out['bytes']=len(data);out['frames']=len(data)/460800
            if len(data)>=460800:
                y=data[-460800:-153600];out['last_frame_y']={'min':min(y),'max':max(y),'mean':sum(y)/len(y)}
    finally:
        if server.poll() is None:
            os.killpg(server.pid,signal.SIGTERM)
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait(timeout=3)
        out['server_exit']=server.returncode
out['log']=log.read_text(errors='replace')[-18000:]
out['dmesg_tail']=subprocess.check_output(['dmesg'],text=True).splitlines()[-50:]
out['server_left_running']=False
print(json.dumps(out,indent=2))
PY
