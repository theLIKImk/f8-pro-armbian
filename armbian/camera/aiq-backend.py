#!/usr/bin/python3
"""Scoped back-camera AIQ worker. Stop when the preview application closes."""
import argparse
import ctypes as C
import fcntl
import os
import signal
import sys
import time
from pathlib import Path

ROOT=Path('/opt/f8-pro-camera/aiq-v6-c4')
parser=argparse.ArgumentParser()
parser.add_argument('--camera',choices=['back','front'],default='back')
args=parser.parse_args()
front=args.camera=='front'
isp='rkisp1-vir0' if front else 'rkisp0-vir0'
iq=ROOT/('iqfiles-front-c4' if front else 'iqfiles-fps14')
dt=Path('/sys/firmware/devicetree/base/chosen/f8-camera-async-trial')
assert dt.read_bytes()==b'c4\0','This camera profile requires C4'
assert os.environ.get('LD_PRELOAD')==str(ROOT/'lib/libf8-aiq-otp.so'),'OTP validation must be enabled'
lock=Path(os.environ['XDG_RUNTIME_DIR'])/'f8-camera-back.lock'
handle=lock.open('a')
try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('Another F8 camera preview is running')

lib=C.CDLL(str(ROOT/'lib/librkaiq.so'))
lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd.argtypes=[C.c_char_p]
lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd.restype=C.c_char_p
nodes=[p for p in Path('/sys/class/video4linux').glob('video*')
       if (p/'name').read_text().strip()=='rkisp_mainpath' and isp in str(p.resolve())]
assert len(nodes)==1,nodes
node='/dev/'+nodes[0].name
name=lib.rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd(node.encode())
assert name and ((b'_f_gc5035 ' in name) if front else name.startswith(b'm00_b_ov8858 ')),name
lib.rk_aiq_uapi2_sysctl_preInit_scene.argtypes=[C.c_char_p,C.c_char_p,C.c_char_p]
lib.rk_aiq_uapi2_sysctl_preInit_scene.restype=C.c_int
assert lib.rk_aiq_uapi2_sysctl_preInit_scene(name,b'normal',b'day')==0
lib.rk_aiq_uapi2_sysctl_init.argtypes=[C.c_char_p,C.c_char_p,C.c_void_p,C.c_void_p]
lib.rk_aiq_uapi2_sysctl_init.restype=C.c_void_p
ctx=lib.rk_aiq_uapi2_sysctl_init(name,str(iq).encode(),None,None)
assert ctx,'Camera engine initialization failed'
lib.rk_aiq_uapi2_sysctl_prepare.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_int]
lib.rk_aiq_uapi2_sysctl_prepare.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_start.argtypes=[C.c_void_p];lib.rk_aiq_uapi2_sysctl_start.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_stop.argtypes=[C.c_void_p,C.c_bool];lib.rk_aiq_uapi2_sysctl_stop.restype=C.c_int
lib.rk_aiq_uapi2_sysctl_deinit.argtypes=[C.c_void_p];lib.rk_aiq_uapi2_sysctl_deinit.restype=None
closing=False
def stop(*_):
    global closing
    if closing:return
    closing=True
    raise SystemExit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
started=False
try:
    width,height=(2592,1944) if front else (3264,2448)
    assert lib.rk_aiq_uapi2_sysctl_prepare(ctx,width,height,0)==0
    assert lib.rk_aiq_uapi2_sysctl_start(ctx)==0
    started=True
    print('F8_CAMERA_AIQ_READY '+node,flush=True)
    while True:time.sleep(.25)
finally:
    if started:lib.rk_aiq_uapi2_sysctl_stop(ctx,False)
    lib.rk_aiq_uapi2_sysctl_deinit(ctx)
    print('F8_CAMERA_AIQ_STOPPED',flush=True)
