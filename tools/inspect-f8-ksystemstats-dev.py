import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
out={}
for name,args in [('dbus',u+['busctl','--user','introspect','org.kde.ksystemstats1','/org/kde/ksystemstats1']),('dev_packages',['dpkg-query','-W','g++','cmake','qt6-base-dev','libksysguard-dev','libkf6coreaddons-dev','libkf6solid-dev','extra-cmake-modules']),('plugin_deps',['ldd','/usr/lib/aarch64-linux-gnu/qt6/plugins/ksystemstats/ksystemstats_plugin_gpu.so']),('disk_deps',['ldd','/usr/lib/aarch64-linux-gnu/qt6/plugins/ksystemstats/ksystemstats_plugin_disk.so']),('disk_udev',['udevadm','info','--query=property','--name=/dev/mmcblk0']),('disk_stat',u+['cat','/sys/class/block/mmcblk0/stat']),('gpu_load',u+['cat','/sys/class/devfreq/fb000000.gpu-panthor/load']),('profiling',['cat','/sys/devices/platform/fb000000.gpu-panthor/profiling'])]:
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=10);out[name]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:out[name]={'error':str(e)}
out['monitor_config_files']=[str(p) for p in Path('/home/likimk/.local/share/plasma-systemmonitor').rglob('*') if p.is_file()] if Path('/home/likimk/.local/share/plasma-systemmonitor').exists() else []
print(json.dumps(out,indent=2))
