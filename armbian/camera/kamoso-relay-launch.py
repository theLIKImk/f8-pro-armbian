#!/usr/bin/python3
"""Stock Kamoso consumes the user-enabled F8 camera relay, never physical ISP nodes."""
import json,os,subprocess,sys,time
from pathlib import Path

try:
    state=json.loads((Path(os.environ['XDG_RUNTIME_DIR'])/'f8-camera-preview-status.json').read_text())
    assert state.get('relay_running') and state.get('state')=='preview'
    assert Path('/sys/class/video4linux/video42/name').read_text().strip()=='F8 Camera Relay'
except (AssertionError,KeyError,OSError,ValueError):
    subprocess.run(['kdialog','--title','兼容相机','--msgbox','请先在 F8 相机中开始预览，并勾选“兼容中继”，然后重新打开 Kamoso。'],timeout=60)
    raise SystemExit(1)
cache=Path.home()/'.cache/f8-kamoso';cache.mkdir(parents=True,exist_ok=True)
plugins=cache/'gst-plugins';plugins.mkdir(exist_ok=True)
source=Path('/usr/lib/aarch64-linux-gnu/gstreamer-1.0')
allowed={p.name:p for p in source.glob('*.so') if p.name!='libgstlibcamera.so'}
for p in plugins.iterdir():
    assert p.is_symlink(),'Unexpected file in private plugin directory'
    if p.name not in allowed:p.unlink()
for name,p in allowed.items():
    dest=plugins/name
    if not dest.is_symlink():dest.symlink_to(p)
config=cache/'relay-config';config.mkdir(exist_ok=True)
preferences=config/'kamosorc'
if not preferences.exists():preferences.write_text('[WebcamSettings]\ndeviceObjectId=/dev/video42\nmirrored=false\n')
env={**os.environ,'QT_QPA_PLATFORM':'wayland','QSG_RHI_BACKEND':'opengl',
     'LD_PRELOAD':'/usr/local/lib/f8-pro/libf8-camera-relay-view.so',
     'GST_PLUGIN_SYSTEM_PATH_1_0':str(plugins),'GST_PLUGIN_PATH_1_0':'',
     'GST_REGISTRY_1_0':str(cache/'gst-relay-registry.bin'),'XDG_CONFIG_HOME':str(config)}
log=cache/('relay-'+time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns()%1000000000)+'.log')
with log.open('w') as output:
    raise SystemExit(subprocess.run(['/usr/bin/kamoso',*sys.argv[1:]],env=env,stdout=output,stderr=subprocess.STDOUT).returncode)
