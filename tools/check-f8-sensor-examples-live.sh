#!/bin/sh
set -eu
python3 -I - <<'PY'
import importlib.util,json,os,queue,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,'/usr/local/lib/f8-pro')
spec=importlib.util.spec_from_file_location('f8_sensor_monitor','/usr/local/lib/f8-pro/sensor-monitor.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from motion_examples_math import GyroPose,mapped
reader=module.Reader();pose=GyroPose();pose.calibrate();samples=0;last={};deadline=time.monotonic()+5
try:
 while time.monotonic()<deadline:
  try:data=reader.messages.get(timeout=.5)
  except queue.Empty:continue
  samples+=1;last=data;m=data['example_matrix'];w=data.get('scaled',{}).get('anglvel');a=data.get('scaled',{}).get('accel')
  if w and a:pose.advance(mapped(m,w),data['monotonic'],mapped(m,a))
  if pose.samples is None and samples>20:break
finally:reader.stop.set();reader.thread.join(timeout=3)
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
p=subprocess.run(['systemctl','--user','restart','f8-sensor-examples-review01.service'],env=env,capture_output=True,text=True,timeout=10)
if p.returncode:
 sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
 p=subprocess.run(['systemd-run','--user','--collect','--unit=f8-sensor-examples-review02','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/local/bin/f8-sensors'],env=env,capture_output=True,text=True,timeout=10)
assert p.returncode==0,p.stderr
time.sleep(2)
print(json.dumps({'samples':samples,'gyro_bias_trial_rad_s':pose.bias,'message':pose.message,'quaternion':pose.q,'matrix_source':last.get('example_matrix_source'),'reader_exited':not reader.thread.is_alive(),'gui_restarted':True,'hardware_or_saved_calibration_changed':False},ensure_ascii=False,indent=2))
PY
