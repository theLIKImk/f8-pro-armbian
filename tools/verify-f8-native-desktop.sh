#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
expected='69056675-4a48-4006-a3f3-5132c00cc6f2'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/etc/f8-pro-native-desktop-t1').is_file()
mount=next(line.split() for line in Path('/proc/mounts').read_text().splitlines() if line.split()[1]=='/')
assert mount[0]=='/dev/mmcblk0p6' and mount[2]=='ext4' and 'rw' in mount[3].split(',')
uuid=subprocess.check_output(['blkid','-s','UUID','-o','value','/dev/mmcblk0p6'],text=True).strip()
assert uuid==expected
session=json.loads(Path('/run/user/1601/f8-desktop/session.json').read_text())
assert session['session_type']=='wayland' and session['desktop']=='KDE'
services={}
for name in ['sddm','NetworkManager','f8-live-prepare','f8-desktop-hardware','f8-live-ssh','f8-live-power']:
    services[name]=subprocess.check_output(['systemctl','is-active',name],text=True).strip()
    assert services[name]=='active',name
gpu=[]
for node in Path('/sys/class/drm').glob('renderD*'):
    driver=node/'device/driver'
    if driver.is_symlink():gpu.append(driver.resolve().name)
assert 'panthor' in gpu
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
keyboard={}
for prop in ['available','enabled']:
    value=subprocess.check_output(prefix+['busctl','--user','get-property','org.kde.KWin','/VirtualKeyboard','org.kde.kwin.VirtualKeyboard',prop],text=True).strip()
    assert value in ['b true','b false'],(prop,value)
    if prop=='available':assert value=='b true',(prop,value)
    keyboard[prop]=value=='b true'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
marker=Path('/var/lib/f8-pro/native-persistence-check.json')
marker.parent.mkdir(parents=True,exist_ok=True)
previous=json.loads(marker.read_text()) if marker.exists() else None
if previous is None:
    marker.write_text(json.dumps({'first_boot_id':boot,'root_uuid':expected,'created_epoch':time.time()})+'\n')
    with marker.open('rb') as f:os.fsync(f.fileno())
    fd=os.open(marker.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
else:assert previous['root_uuid']==expected
print(json.dumps({'scope':'Native writable Armbian desktop acceptance','root_mount':mount[:4],
 'root_uuid':uuid,'kernel':os.uname().release,'session':session,'services':services,'gpu_drivers':gpu,
 'keyboard':keyboard,'boot_id':boot,'persistence_marker_written':previous is None,
 'reboot_persistence_confirmed':bool(previous and previous['first_boot_id']!=boot)},indent=2))
PY
