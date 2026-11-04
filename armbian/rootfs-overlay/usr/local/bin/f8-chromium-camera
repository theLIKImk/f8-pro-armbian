#!/usr/bin/python3
"""Dedicated Chromium profile with the same real-relay-only view as Kamoso."""
import os,sys
sys.path.insert(0,'/usr/local/lib/f8-pro')
from browser_pose_bridge import launch
from pathlib import Path
library=Path('/usr/local/lib/f8-pro/libf8-camera-relay-view.so');assert library.is_file()
folder=Path.home()/'.config/chromium-f8-camera';folder.mkdir(parents=True,exist_ok=True)
cache=Path.home()/'.cache/f8-browser-camera';cache.mkdir(parents=True,exist_ok=True)
env={**os.environ,'LD_PRELOAD':str(library)}
targets=sys.argv[1:] or ['file:///usr/local/share/f8-pro/camera-browser-test.html']
with (cache/'browser.log').open('a') as log:
    os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
    raise SystemExit(launch(['/usr/bin/chromium','--no-first-run','--no-default-browser-check','--ozone-platform=wayland','--enable-features=GenericSensorExtraClasses','--enable-blink-features=SensorExtraClasses','--user-data-dir='+str(folder),*targets],env,log))
