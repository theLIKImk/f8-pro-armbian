"""Use public API with the board's existing manual WB gains; diagnostic only."""
import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'local/hardware/camera-c4-aiq-fps14-runner.sh').read_text()
s=s.replace("derived=root/'iqfiles-fps14';assert not derived.exists();derived.mkdir()","derived=root/'iqfiles-fps14';assert derived.is_dir()")
s=s.replace("(derived/name).write_text(json.dumps(changed)+'\\n')","assert json.loads((derived/name).read_text())==changed")
s=s.replace('back-aiq-fps14.log','back-aiq-fps14-apiwb.log').replace('back-aiq-fps14-640x480.nv12','back-aiq-fps14-apiwb-640x480.nv12')
anchor="print('INIT',bool(ctx),flush=True);assert ctx\n"
wb='''class WB(C.Structure):
    _fields_=[('r',C.c_float),('gr',C.c_float),('gb',C.c_float),('b',C.c_float)]
lib.rk_aiq_uapi2_setWBMode.argtypes=[C.c_void_p,C.c_int];lib.rk_aiq_uapi2_setWBMode.restype=C.c_int
lib.rk_aiq_uapi2_setMWBGain.argtypes=[C.c_void_p,C.POINTER(WB)];lib.rk_aiq_uapi2_setMWBGain.restype=C.c_int
lib.rk_aiq_uapi2_getWBGain.argtypes=[C.c_void_p,C.POINTER(WB)];lib.rk_aiq_uapi2_getWBGain.restype=C.c_int
g=WB(1.2261,1.0,1.0,2.3158)
print('SET_WB_MODE',lib.rk_aiq_uapi2_setWBMode(ctx,1),flush=True)
print('SET_WB_GAIN',lib.rk_aiq_uapi2_setMWBGain(ctx,C.byref(g)),flush=True)
'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+wb)
s=s.replace("print('STOP',lib.rk_aiq_uapi2_sysctl_stop(ctx,False),flush=True)","g=WB();print('GET_WB_GAIN',lib.rk_aiq_uapi2_getWBGain(ctx,C.byref(g)),[g.r,g.gr,g.gb,g.b],flush=True)\n    print('STOP',lib.rk_aiq_uapi2_sysctl_stop(ctx,False),flush=True)")
r=P/'local/hardware/camera-c4-aiq-wb-api-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/'local/hardware/camera-c4-aiq-wb-api-test01.json').write_text(p.stdout)
print('Saved manual WB API comparison')
