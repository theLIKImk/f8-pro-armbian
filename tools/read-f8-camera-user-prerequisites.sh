#!/bin/sh
set -eu
id
python3 -I - <<'PY'
import importlib.util,json,os,subprocess
checks={}
for element in ['v4l2src','videoconvert','fdsink']:
 try:
  p=subprocess.run(['gst-inspect-1.0',element],capture_output=True,text=True,timeout=15)
  checks[element]={'exit':p.returncode,'stderr':p.stderr}
 except subprocess.TimeoutExpired:checks[element]={'timeout':True}
p=subprocess.run(['qv4l2','--help'],env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},capture_output=True,text=True,timeout=8)
checks['qv_help']={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps({'qt6':importlib.util.find_spec('PyQt6') is not None,'gst':checks,
 'camera_devices_rw':{n:os.access(n,os.R_OK|os.W_OK) for n in ['/dev/video22','/dev/v4l-subdev5','/dev/video29','/dev/video30']}}))
PY
