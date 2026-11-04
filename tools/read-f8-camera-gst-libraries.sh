#!/bin/sh
set -eu
python3 -I - <<'PY'
import ctypes as C
from pathlib import Path
g=C.CDLL('libgstreamer-1.0.so.0');g.gst_init(None,None)
g.gst_version_string.restype=C.c_char_p
print('VERSION',g.gst_version_string())
print('\n'.join(x for x in Path('/proc/self/maps').read_text().splitlines() if 'gstreamer' in x or 'video4linux' in x))
for name,ret,args in [('gst_device_provider_factory_find',C.c_void_p,[C.c_char_p]),('gst_plugin_feature_get_rank',C.c_uint,[C.c_void_p]),('gst_plugin_feature_get_plugin_name',C.c_char_p,[C.c_void_p])]:
 f=getattr(g,name);f.restype=ret;f.argtypes=args
for n in [b'v4l2deviceprovider',b'libcameraprovider',b'libcameradeviceprovider']:
 p=g.gst_device_provider_factory_find(n);print(n,p, (g.gst_plugin_feature_get_rank(p),g.gst_plugin_feature_get_plugin_name(p)) if p else '')
PY
ls -l /usr/lib/aarch64-linux-gnu/libgstreamer* /usr/local/lib/*gstreamer* 2>/dev/null || true
