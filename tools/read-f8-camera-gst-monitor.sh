#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,ctypes as C
os.environ['GST_DEBUG']='v4l2deviceprovider:6,v4l2:5,devicemonitor:6'
os.environ['GST_PLUGIN_FEATURE_RANK']='libcameraprovider:0,v4l2deviceprovider:256'
g=C.CDLL('libgstreamer-1.0.so.0')
for name,ret,args in [('gst_init',None,[C.c_void_p,C.c_void_p]),('gst_device_monitor_new',C.c_void_p,[]),('gst_caps_from_string',C.c_void_p,[C.c_char_p]),('gst_device_monitor_add_filter',C.c_uint,[C.c_void_p,C.c_char_p,C.c_void_p]),('gst_device_monitor_start',C.c_int,[C.c_void_p]),('gst_device_monitor_get_devices',C.c_void_p,[C.c_void_p]),('gst_device_monitor_stop',None,[C.c_void_p])]:
 f=getattr(g,name);f.restype=ret;f.argtypes=args
g.gst_init(None,None)
g.gst_device_provider_factory_find.argtypes=[C.c_char_p];g.gst_device_provider_factory_find.restype=C.c_void_p
g.gst_plugin_feature_set_rank.argtypes=[C.c_void_p,C.c_uint]
g.gst_plugin_feature_set_rank(g.gst_device_provider_factory_find(b'libcameraprovider'),0)
m=g.gst_device_monitor_new();g.gst_device_monitor_set_show_all_devices.argtypes=[C.c_void_p,C.c_int];g.gst_device_monitor_set_show_all_devices(m,1)
caps=g.gst_caps_from_string(b'video/x-raw');g.gst_device_monitor_add_filter(m,b'Video/Source',caps)
print('GST_DEVICE_MONITOR_START',g.gst_device_monitor_start(m),'DEVICES',g.gst_device_monitor_get_devices(m),flush=True);g.gst_device_monitor_stop(m)
out={}
commands={
 'monitor':['python3','-c',"import gi;gi.require_version('Gst','1.0');from gi.repository import Gst;Gst.init(None);m=Gst.DeviceMonitor.new();m.add_filter('Video/Source',Gst.Caps.from_string('video/x-raw'));print('START',m.start());[(print(d.get_display_name(),d.get_caps().to_string(),d.get_properties().to_string())) for d in m.get_devices()];m.stop()"],
 'formats':['v4l2-ctl','-d','/dev/video22','--list-formats-ext'],
 'health':['systemctl','--failed','--no-pager']}
for name,args in commands.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=20,env={**os.environ,'GST_DEBUG':'v4l2deviceprovider:6,v4l2:4'});out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
