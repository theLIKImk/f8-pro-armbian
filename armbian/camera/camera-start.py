#!/usr/bin/python3
"""C2 cold-start completion; never unbind a live media device."""
import fcntl,json,os,struct,subprocess,time
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
assert (dt/'chosen/f8-camera-trial').read_bytes()==b'c2\0'
for module in ['gc5035','ov8858']:subprocess.run(['modprobe',module],check=True,timeout=12)
expected={'5-0037':'gc5035','5-0036':'ov8858'}
deadline=time.monotonic()+8
while True:
    bindings={name:(Path('/sys/bus/i2c/devices')/name/'driver').resolve().name for name in expected}
    if bindings==expected:break
    assert time.monotonic()<deadline,('Sensor binding incomplete',bindings)
    time.sleep(.2)
for name in ['fdcb0000.rkisp','fdcc0000.rkisp']:
    p=Path('/sys/bus/platform/devices')/name/'driver';assert p.exists() and p.resolve().name=='rkisp_hw',name
probed={}
for name in ['rkisp0-vir0','rkisp1-vir0','rkcif-mipi-lvds2-sditf','rkcif-mipi-lvds3-sditf']:
    p=Path('/sys/bus/platform/devices')/name/'driver'
    already=p.exists()
    if not already:Path('/sys/bus/platform/drivers_probe').write_text(name+'\n')
    probed[name]={'already_bound':already,'driver':p.resolve().name if p.exists() else None}
blanking={}
if (dt/'chosen/f8-camera-async-trial').exists() and (dt/'chosen/f8-camera-async-trial').read_bytes()==b'c4\0':
    # Keep ISP-online blanking >=1000us (factory defaults log 933/700us).
    # Apply only via standard V4L2 controls; preserve larger existing values.
    for sensor,minimum in [('m01_f_gc5035 5-0037',80),('m00_b_ov8858 5-0036',64)]:
        try:
            nodes=[p for p in Path('/sys/class/video4linux').glob('v4l-subdev*') if (p/'name').read_text().strip()==sensor]
            assert len(nodes)==1,(sensor,nodes)
            fd=os.open('/dev/'+nodes[0].name,os.O_RDWR|os.O_NONBLOCK)
            try:
                value=bytearray(struct.pack('Ii',0x009e0901,0))
                fcntl.ioctl(fd,0xc008561b,value,True)
                before=struct.unpack('Ii',value)[1];wanted=max(minimum,before)
                fcntl.ioctl(fd,0xc008561c,struct.pack('Ii',0x009e0901,wanted))
                fcntl.ioctl(fd,0xc008561b,value,True)
                after=struct.unpack('Ii',value)[1];assert after==wanted,(sensor,after,wanted)
                blanking[sensor]={'before':before,'after':after,'minimum':minimum}
            finally:os.close(fd)
        except Exception as e:blanking[sensor]={'error':str(e)}
print(json.dumps({'sensor_bindings':bindings,'late_initial_probes':probed,
 'c4_online_blanking':blanking,
 'live_device_unbound':False,'capture_started':False},indent=2))
