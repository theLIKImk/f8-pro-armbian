import sys,os,json,time
from pathlib import Path
sys.path.insert(0,'/usr/local/lib/f8-pro')
from browser_pose_bridge import launch
folder=Path.home()/'.cache/f8-browser-pose-test';folder.mkdir(parents=True,exist_ok=True)
env=dict(os.environ);camera=Path('/usr/local/lib/f8-pro/libf8-camera-relay-view.so')
if camera.exists():env['LD_PRELOAD']=str(camera)
args=['/usr/bin/chromium','--no-first-run','--no-default-browser-check','--ozone-platform=wayland','--enable-features=GenericSensorExtraClasses','--enable-blink-features=SensorExtraClasses','--user-data-dir='+str(folder/'profile'),'https://www.codertools.net/tools/motion-sensor-test.php?lang=zh']
with (folder/'browser.log').open('a') as log:raise SystemExit(launch(args,env,log))
