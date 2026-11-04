from pathlib import Path
import json,importlib.util,subprocess,re
p=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
s=importlib.util.spec_from_file_location('connection',p/'tools/build-plasma-activities.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
r=json.loads((p/'analysis/arch-gpu/qt-eglfs-smoke.json').read_text())['remote_work_directory']
assert re.fullmatch(r'/tmp/f8-qt-gpu-[A-Za-z0-9]{8}',r)
subprocess.run(['scp',*c.OPTIONS,*[str(p/'tools/qt-gpu-smoke'/f) for f in ('main.cpp','main.qml','plasma.qml','CMakeLists.txt')],c.HOST+':'+r+'/'],check=True,timeout=30)
c.ssh('cmake -S '+r+' -B '+r+'/build -G Ninja -DCMAKE_BUILD_TYPE=Release',check=True,timeout=60)
c.ssh('cmake --build '+r+'/build --parallel 2',check=True,timeout=90)
