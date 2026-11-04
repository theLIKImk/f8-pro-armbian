#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='9df01d2b-d624-4364-8d3d-a06ff6847720'
usb=Path('/sys/bus/usb/devices/1-1');part=Path('/sys/class/block/sda1')
assert (usb/'idVendor').read_text().strip()=='152d' and (usb/'idProduct').read_text().strip()=='0583'
assert str(part.resolve()).startswith(str(usb.resolve())+'/')
assert not any(s.split()[0].startswith('/dev/sda') for s in Path('/proc/mounts').read_text().splitlines())
where=Path('/run/f8/usb-exfat-readonly01');where.mkdir(exist_ok=False)
def cmd(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'device':'/dev/sda1','filesystem':'exfat','requested_options':['ro','nosuid','nodev','noexec'],'user_file_contents_read':False,'write_test_performed':False}
mounted=False
try:
    result['mount']=cmd(['mount','-t','exfat','-o','ro,nosuid,nodev,noexec','/dev/sda1',str(where)])
    assert result['mount']['exit']==0,result['mount']
    mounted=True
    record=next(s.split() for s in Path('/proc/mounts').read_text().splitlines() if s.split()[1]==str(where))
    assert record[2]=='exfat' and 'ro' in record[3].split(',')
    result['verified_mount_options']=record[3]
    with os.scandir(where) as entries:
        count=0
        for entry in entries:
            count+=1
            if count==16:break
    result['directory_metadata_read_passed']=True;result['entries_seen_capped_at_16']=count
finally:
    if mounted:
        result['unmount']=cmd(['umount',str(where)])
        assert result['unmount']['exit']==0,result['unmount']
    result['left_mounted']=any(s.split()[1]==str(where) for s in Path('/proc/mounts').read_text().splitlines())
    (where/'test-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
