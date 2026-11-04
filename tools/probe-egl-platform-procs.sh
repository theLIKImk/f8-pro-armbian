set -eu
env LD_LIBRARY_PATH=/opt/f8-pro/vendor-gpu-g13p0-20261028/lib python3 - <<'PY'
import ctypes,json
x=ctypes.CDLL('/opt/f8-pro/vendor-gpu-g13p0-20261028/lib/libEGL.so.1');x.eglGetProcAddress.argtypes=[ctypes.c_char_p];x.eglGetProcAddress.restype=ctypes.c_void_p
print(json.dumps({n:bool(x.eglGetProcAddress(n.encode())) for n in ['eglCreatePlatformWindowSurfaceEXT','eglCreatePlatformWindowSurface','eglCreateWindowSurface']},indent=2))
PY
