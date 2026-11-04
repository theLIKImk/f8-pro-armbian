#!/usr/bin/python3
"""Launch stock Kamoso with this board's scoped rear-camera AIQ worker."""
import os,signal,subprocess,sys,time
from pathlib import Path

cache=Path.home()/'.cache/f8-kamoso';cache.mkdir(parents=True,exist_ok=True)
log=cache/(time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns()%1000000000)+'.log')
engine=None;app=None
def stop(*_):raise SystemExit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
    # Only close our earlier test window; it does not record video.
    subprocess.run(['systemctl','--user','stop','f8-camera-preview-review01.service'],capture_output=True,timeout=10)
    with log.open('w') as output:
        worker_env={**os.environ,'LD_PRELOAD':'/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so','PYTHONUNBUFFERED':'1'}
        engine=subprocess.Popen(['/usr/bin/python3','-u','/usr/local/lib/f8-pro/aiq-backend.py'],env=worker_env,stdout=output,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+7
        while time.monotonic()<deadline:
            if engine.poll() is not None:break
            if 'F8_CAMERA_AIQ_READY ' in log.read_text(errors='replace'):break
            time.sleep(.1)
        assert engine.poll() is None and 'F8_CAMERA_AIQ_READY ' in log.read_text(errors='replace'),'Camera engine failed; see '+str(log)
        # libcamera hides the V4L2 provider even when it finds no usable camera.
        # Private plugin view keeps distribution binaries untouched.
        plugins=cache/'gst-plugins';plugins.mkdir(exist_ok=True)
        source=Path('/usr/lib/aarch64-linux-gnu/gstreamer-1.0')
        allowed={p.name:p for p in source.glob('*.so') if p.name!='libgstlibcamera.so'}
        for p in plugins.iterdir():
            assert p.is_symlink(),'Unexpected file in private plugin directory'
            if p.name not in allowed:p.unlink()
        for name,p in allowed.items():
            dest=plugins/name
            if not dest.is_symlink():dest.symlink_to(p)
        env={**os.environ,'QT_QPA_PLATFORM':'wayland','QSG_RHI_BACKEND':'opengl',
             'GST_PLUGIN_SYSTEM_PATH_1_0':str(plugins),'GST_PLUGIN_PATH_1_0':'',
             'GST_REGISTRY_1_0':str(cache/'gst-registry.bin')}
        app=subprocess.Popen(['/usr/bin/kamoso',*sys.argv[1:]],env=env,stdout=output,stderr=subprocess.STDOUT)
        raise SystemExit(app.wait())
except AssertionError as e:
    subprocess.run(['kdialog','--title','Kamoso 相机','--error',str(e)],timeout=30)
finally:
    for process in [app,engine]:
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
