"""Add ABI-verified F8 touch trial to the hardware-tested G2 boot, no root repack."""
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-graphics-g2'
out=P/'outputs/armbian/official-f8-touch-g3';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed G3'
prior=json.loads((base/'preflight.json').read_text())
assert prior['hardware_fix_verified'] and prior['hardware_test_performed']
module_dir=P/'armbian/touch/official-6.1.115-f8'
modcheck=json.loads((module_dir/'module-check.json').read_text())
algo=json.loads((module_dir/'algorithm-version-check.json').read_text())
assert modcheck['all_import_crcs_match_actual_official_modules'] and algo['version_ids_equal']
module=(module_dir/modcheck['module']).read_bytes()
assert hashlib.sha256(module).hexdigest()==modcheck['sha256']
image=base/prior['candidate_file'];blob=image.read_bytes()
assert hashlib.sha256(blob).hexdigest()==prior['candidate_sha256']
work=Path('/var/tmp/f8-pro-armbian/official-touch-g3');work.mkdir(exist_ok=True)
fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];a=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    data=blob[a:a+size];assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(data)
before=fdt((work/'fdt').read_bytes());node='/i2c@feac0000/ts@40'
assert before[node]['status']==b'disabled\0'
subprocess.run(['fdtput','-t','s',str(work/'fdt'),node,'compatible','f8-pro,gslx680-shuping-eval'],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),node,'status','okay'],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/','model','F8-PRO official Armbian G3 touch trial'],check=True)
after=fdt((work/'fdt').read_bytes());expected=copy.deepcopy(before)
expected[node]['compatible']=b'f8-pro,gslx680-shuping-eval\0';expected[node]['status']=b'okay\0'
expected['/']['model']=b'F8-PRO official Armbian G3 touch trial\0'
assert after==expected,'Only touch compatible/status and model may change'
for key in ['reg','touch-gpio','reset-gpio','pinctrl-0']:
    assert after[node][key]==before[node][key]
factory=(P/'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
assert struct.unpack_from('<I',factory,0x14864e4)[0]==0xd2800023 # IRQ flags x3=1 before request_threaded_irq.
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
old_records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()))
old={n:b for n,_,b in old_records}
assets=P/'armbian/official-graphics'
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
payloads={'f8_gsl_shuping.ko':module,'touch-events.py':(assets/'touch-events.py').read_bytes(),
          'graphics-run':(assets/'touch-graphics-run.sh').read_bytes(),
          'wayland-client':(assets/'touch-wayland-client.sh').read_bytes()}
for name,find,replace in [('f8-official-graphics.service','RuntimeMaxSec=85','RuntimeMaxSec=190'),
                          ('f8-official-wayland.service','RuntimeMaxSec=35','RuntimeMaxSec=110'),
                          ('f8-official-report.timer','OnActiveSec=110s','OnActiveSec=210s')]:
    text=(root/'etc/systemd/system'/name).read_text();assert find in text
    text=text.replace(find,replace)
    if name=='f8-official-wayland.service':text=text.replace('StandardInput=tty','StandardInput=tty\nStandardOutput=journal\nStandardError=journal')
    payloads[name]=text.encode()
# Verify only newly named temporary units; do not overwrite root's existing units.
temporary=[]
try:
    for name,data in payloads.items():
        if name.endswith(('.service','.timer')):
            dest=root/'etc/systemd/system'/('g3-verify-'+name);assert not dest.exists()
            dest.write_bytes(data);dest.chmod(0o644);temporary.append(dest)
    result=subprocess.run(['systemd-analyze','--root='+str(root),'--man=no','verify',*[x.name for x in temporary]],capture_output=True,text=True)
    (out/'updated-unit-verification.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr
finally:
    for path in temporary:path.unlink()
probe=root/'tmp/f8-g3-touch-events.py';output=root/'tmp/f8-g3-touch-events.json'
assert not probe.exists() and not output.exists()
probe.write_bytes(payloads['touch-events.py'])
try:
    r=subprocess.run(['chroot',str(root),'/usr/bin/python3','-I','/tmp/f8-g3-touch-events.py',
                      '--seconds','0','--discovery-seconds','0','--output','/tmp/f8-g3-touch-events.json'],capture_output=True,text=True,timeout=30)
    negative=json.loads(output.read_text());assert r.returncode==1 and not negative['device_found']
finally:
    probe.unlink()
    if output.exists():output.unlink()
init=old['init'].replace(b'ARMBIAN-G2',b'ARMBIAN-G3')
anchor=b"echo 'Verified lower image"
assert init.count(anchor)==1
install=b'''for asset in /f8-g3-assets/*; do
    name=${asset##*/}
    case "$name" in
        *.service|*.timer) destination="/mnt/root/etc/systemd/system/$name"; mode=0644;;
        *.ko|*.py) destination="/mnt/root/usr/libexec/f8-pro/$name"; mode=0644;;
        *) destination="/mnt/root/usr/libexec/f8-pro/$name"; mode=0755;;
    esac
    cp "$asset" "$destination" || fail touch-asset-copy
    chmod "$mode" "$destination" || fail touch-asset-mode
done
'''
init=init.replace(anchor,install+anchor)
logger=old['f8-evaluation-report'].replace(b'ARMBIAN-G2',b'ARMBIAN-G3').replace(b'F8PROAG2',b'F8PROAG3').replace(b'f8_official_armbian_g2',b'f8_official_armbian_g3')
anchor=b'    cat /etc/armbian-release >"$disk/ARMBIAN.TXT" 2>&1\n';assert anchor in logger
logger=logger.replace(anchor,anchor+b'''    [ ! -f /run/f8/touch-events.json ] || cp /run/f8/touch-events.json "$disk/TOUCH.JSON"
    [ ! -f /run/f8/touch-capture.log ] || cp /run/f8/touch-capture.log "$disk/TOUCHLOG.TXT"
    cat /proc/bus/input/devices >"$disk/INPUT.TXT"
    cat /proc/interrupts >"$disk/IRQ.TXT"
    ls -l /sys/bus/i2c/devices/4-0040/driver >"$disk/TOUCHDRV.TXT" 2>&1
    timeout 10 journalctl -b -u f8-official-wayland.service --no-pager >/run/f8/wayland-all.log 2>&1
    { head -n 180 /run/f8/wayland-all.log; echo '--- tail ---'; tail -n 180 /run/f8/wayland-all.log; } >"$disk/KWIN.TXT"
    grep -Ei 'OpenGL|EGL|renderer|Mesa|G610|llvmpipe|softpipe|libinput|touch' /run/f8/wayland-all.log | head -n 200 >"$disk/RENDER.TXT"
''')
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG3',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
new=[]
for name,values,body in old_records:
    data={'init':init,'f8-evaluation-report':logger,'f8-firstboot-logs.img':fat.read_bytes()}.get(name,body)
    fields=list(values);fields[6]=len(data);new.append((name,fields,data))
def add(name,data,mode):
    fields=[10000+len(new),mode,0,0,1,0,len(data),0,0,0,0,0,0]
    new.append((name,fields,data))
add('f8-g3-assets',b'',stat.S_IFDIR|0o755)
for name,data in payloads.items():add('f8-g3-assets/'+name,data,stat.S_IFREG|0o644)
cpio=helper.cpio_write(new);check={n:b for n,_,b in helper.cpio_read(cpio)}
assert check['f8-g3-assets/f8_gsl_shuping.ko']==module
for name,data in payloads.items():assert check['f8-g3-assets/'+name]==data
busybox=work/'busybox';busybox.write_bytes(old['bin/busybox']);busybox.chmod(0o755)
for name,data in [('init',init),('report',logger),*[(n,b) for n,b in payloads.items() if n in ['graphics-run','wayland-client']]]:
    path=work/(name+'.sh');path.write_bytes(data)
    subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(path)],check=True)
(work/'ramdisk').write_bytes(gzip.compress(cpio,compresslevel=6,mtime=0))
its=Path('/var/tmp/f8-pro-armbian/official-graphics-g2/boot.its').read_text().replace('G2 NOT APPROVED','G3 TOUCH NOT APPROVED')
(work/'boot.its').write_text(its)
candidate=out/'BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G3_CANDIDATE.img'
listing=subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(candidate)],cwd=work,text=True)
(out/'mkimage.txt').write_text(listing)
data=candidate.read_bytes();tree=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    props=tree['/images/'+name];a=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    value=data[a:a+size];assert value==(work/name).read_bytes()
    assert hashlib.sha256(value).digest()==tree['/images/'+name+'/hash']['value']
assert candidate.stat().st_size<64*1024*1024
runtime=struct.unpack_from('<Q',(work/'kernel').read_bytes(),16)[0]
ranges={'kernel':(0x400000,0x400000+runtime),'dtb':(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
        'initrd':(0xa200000,0xa200000+(work/'ramdisk').stat().st_size)}
mem=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(x['base'],16),int(x['base'],16)+int(x['size'],16)) for x in mem['banks']]
for n,(a,b) in ranges.items():assert any(x<=a<b<=y for x,y in banks),n
for n,(a,b) in ranges.items():
    for other,(x,y) in ranges.items():
        if n!=other:assert not(a<y and x<b)
report={'scope':'Offline-ready F8 touch/Wayland trial on hardware-tested G2 GPU baseline; touch untested',
        'candidate_file':candidate.name,'candidate_bytes':candidate.stat().st_size,'candidate_sha256':hashlib.sha256(data).hexdigest(),
        'base_g2_sha256':prior['candidate_sha256'],'official_kernel_unchanged':True,'rootfs_unchanged':True,
        'touch_module_sha256':modcheck['sha256'],'all_48_imports_verified_against_actual_official_modules':True,
        'algorithm_version_matches_stock_and_factory':True,'algorithm_full_equivalence_proven':False,
        'touch_dt_only_changes':['compatible','status'],'irq_reset_pinctrl_unchanged':True,
        'factory_irq_rising_static_check_passed':True,'touch_input_ranges':[800,1280],
        'new_unit_options_verified':True,'arm64_no_touch_capture_rejected':negative,
        'event_capture_seconds':110,'wayland_duration_seconds':90,'report_timer_seconds':210,
        'compositor_stdout_stderr_to_journal':True,'log_volume':'F8AG3',
        'payload_sha256':{name:hashlib.sha256(value).hexdigest() for name,value in payloads.items()},
        'fit_payload_hashes_verified':True,'layout_with_12k_pad_verified':True,
        'charging_enabled':False,'ready_for_user_coordinated_trial':True,'deployment_performed':False,
        'hardware_test_performed':False}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'touch-g3.dtb').write_bytes((work/'fdt').read_bytes())
print(json.dumps({k:v for k,v in report.items() if k not in ['payload_sha256','arm64_no_touch_capture_rejected']},indent=2))
