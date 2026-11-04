"""Convert a real retained NV12 frame for an independent ffmpeg comparison."""
import ctypes as C,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
so=Path('/var/tmp/f8-pro-armbian/camera-aiq-audit/libf8-camera-pixels-host.so')
subprocess.run(['gcc','-shared','-fPIC','-O3','-Wall','-Wextra','-Werror',str(P/'armbian/camera/camera-pixels.c'),'-o',str(so)],check=True)
lib=C.CDLL(str(so));fn=lib.f8_nv12_rgb
fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_uint];fn.restype=C.c_int
folder=P/'local/hardware/camera-c4-frames'
data=(folder/'back-aiq-fps14-otp-user-long-02-640x480.nv12').read_bytes();assert len(data)==460800
source=C.create_string_buffer(data);target=C.create_string_buffer(921600)
assert fn(source,len(data),target,len(target),640,480)==0
(folder/'converter-rgb.raw').write_bytes(target.raw)
print('Converted real retained frame; compare with full-range BT.601 ffmpeg output')
