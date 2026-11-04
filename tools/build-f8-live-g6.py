"""Add Wi-Fi SSH, continuous passive telemetry and status VT to verified G5."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-power-g5';prior=json.loads((base/'preflight.json').read_text())
assert prior['power_readout_hardware_verified']
fixture=json.loads((P/'analysis/armbian/live-g6/setup-fixture-systemd-r4.json').read_text())
assert fixture['provisioning_has_proc_dev_run'] and fixture['existing_firmware_symlink_replacement_passed']
out=P/'outputs/armbian/official-f8-live-g6-r6';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed G6'
work=Path('/var/tmp/f8-pro-armbian/official-live-g6-r6');work.mkdir(exist_ok=True)
blob=(base/prior['candidate_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['candidate_sha256']
fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];start=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    data=blob[start:start+size];assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(data)
before=fdt((work/'fdt').read_bytes());expected=copy.deepcopy(before)
factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
refs={v['phandle']:k for k,v in before.items() if 'phandle' in v}
oldrefs={v['phandle']:k for k,v in factory.items() if 'phandle' in v}
def resolve(tree,refs,path,prop):
    return [refs[tree[path][prop][i:i+4]] for i in range(0,len(tree[path][prop]),4)]
wifi='/wireless-wlan';pci='/pcie@fe190000';phy='/phy@fee00000'
# Compare physical wiring across kernels without treating numeric handles as identities.
for key in ['wifi_chip_type']:
    assert before[wifi][key]==factory[wifi][key]
for key in ['WIFI,poweren_gpio','WIFI,host_wake_irq']:
    a,b=before[wifi][key],factory[wifi][key]
    assert a[4:]==b[4:] and refs[a[:4]]==oldrefs[b[:4]]
assert before[pci]['reset-gpios'][4:]==factory[pci]['reset-gpios'][4:]
assert refs[before[pci]['reset-gpios'][:4]]==oldrefs[factory[pci]['reset-gpios'][:4]]
assert refs[before[pci]['phys'][:4]]==oldrefs[factory[pci]['phys'][:4]]==phy
for node in [wifi,pci]:
    a=resolve(before,refs,node,'pinctrl-0');b=resolve(factory,oldrefs,node,'pinctrl-0')
    assert len(a)==len(b)
    for left,right in zip(a,b):
        ar,br=before[left]['rockchip,pins'],factory[right]['rockchip,pins']
        assert len(ar)==len(br)
        for i in range(0,len(ar),16):
            assert ar[i:i+12]==br[i:i+12]
            ac,bc=before[refs[ar[i+12:i+16]]],factory[oldrefs[br[i+12:i+16]]]
            assert {k:v for k,v in ac.items() if k!='phandle'}=={k:v for k,v in bc.items() if k!='phandle'}
for node in [wifi,pci,phy]:
    assert before[node]['status']==b'disabled\0'
    subprocess.run(['fdtput','-t','s',str(work/'fdt'),node,'status','okay'],check=True)
    expected[node]['status']=b'okay\0'
model='F8-PRO official Armbian G6 WiFi SSH live diagnostics'
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/','model',model],check=True)
expected['/']['model']=model.encode()+b'\0'
assert fdt((work/'fdt').read_bytes())==expected
assert expected['/i2c@fec80000/charger@6a']['status']==b'disabled\0'
spec=importlib.util.spec_from_file_location('helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()));old={n:b for n,_,b in records}
asset=P/'armbian/official-graphics'
payloads={name:(asset/name).read_bytes() for name in ['live-setup.sh','live-firmware-setup.sh','live-power.sh','live-network.sh','live-status.py']}
payloads['power-refresh.py']=(asset/'power-refresh.py').read_bytes()
payloads['bq-adc-oneshot.py']=(P/'armbian/power/bq-adc-oneshot.py').read_bytes()
payloads.update({
 'f8-live-prepare.service':b'''[Unit]
Description=Prepare RAM-only test network and SSH after virtual filesystems exist
After=basic.target
Before=NetworkManager.service f8-live-ssh.service f8-live-network.service
[Service]
Type=oneshot
ExecStart=/bin/sh /usr/libexec/f8-pro/live-setup.sh
RemainAfterExit=yes
TimeoutStartSec=45
''',
 'f8-live-ssh.service':b'''[Unit]
Description=F8 test SSH using preserved host identity and key authentication
Wants=systemd-user-sessions.service
Requires=f8-live-prepare.service
After=basic.target systemd-user-sessions.service f8-live-prepare.service
[Service]
Type=exec
ExecStartPre=/usr/sbin/sshd -t -f /run/f8/sshd_config
ExecStart=/usr/sbin/sshd -D -e -f /run/f8/sshd_config
Restart=on-failure
RestartSec=3
''',
 'f8-live-network.service':b'''[Unit]
Description=F8 official WiFi module and DHCP
Wants=NetworkManager.service
Requires=f8-live-prepare.service
After=NetworkManager.service f8-live-prepare.service
[Service]
Type=oneshot
ExecStart=/bin/sh /usr/libexec/f8-pro/live-network.sh
RemainAfterExit=yes
TimeoutStartSec=100
''',
 'f8-live-power.service':b'''[Unit]
Description=F8 passive power telemetry every ten seconds
After=basic.target
[Service]
Type=exec
ExecStart=/bin/sh /usr/libexec/f8-pro/live-power.sh
Restart=on-failure
RestartSec=3
''',
 'f8-live-status.service':b'''[Unit]
Description=F8 boot status on VT2
After=basic.target
[Service]
Type=exec
ExecStart=/usr/bin/python3 -I /usr/libexec/f8-pro/live-status.py
Restart=on-failure
RestartSec=3
''',
 'f8-official-graphics.target':b'''[Unit]
Description=F8 live SSH and Wayland hardware tests
Requires=basic.target
After=basic.target
Wants=f8-official-graphics.service f8-official-report.timer f8-live-prepare.service f8-live-ssh.service f8-live-network.service f8-live-power.service f8-live-status.service systemd-timesyncd.service
AllowIsolate=yes
'''})
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG6',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
new=[];changed=[]
for name,values,body in records:
    data=body
    if name in ['init','f8-evaluation-report']:
        data=data.replace(b'ARMBIAN-G5',b'ARMBIAN-G6').replace(b'F8PROAG5',b'F8PROAG6').replace(b'f8_official_armbian_g5',b'f8_official_armbian_g6')
    if name=='init':
        assert b'*.service|*.timer)' in data
        data=data.replace(b'*.service|*.timer)',b'*.service|*.timer|*.target)')
        anchor=b"echo 'Verified lower image";assert anchor in data
        data=data.replace(anchor,b'/bin/sh /f8-g3-assets/live-firmware-setup.sh || fail live-firmware\n'+anchor)
    elif name=='f8-evaluation-report':
        anchor=b'    cat /etc/armbian-release >"$disk/ARMBIAN.TXT" 2>&1\n';assert anchor in data
        data=data.replace(anchor,anchor+b'''    [ ! -f /run/f8/power-current.json ] || cp /run/f8/power-current.json "$disk/POWER2.JSON"
    [ ! -f /run/f8/network-start.log ] || cp /run/f8/network-start.log "$disk/NETWORK.TXT"
    ip -4 -o addr show scope global >"$disk/IP.TXT" 2>&1
    ss -ltn >"$disk/PORTS.TXT" 2>&1
    timeout 10 journalctl -b -u f8-live-prepare.service -u f8-live-ssh.service -u f8-live-network.service -u NetworkManager.service -n 150 --no-pager >"$disk/LIVELOG.TXT" 2>&1
    timeout 10 journalctl -b -u f8-live-prepare.service --no-pager >"$disk/SETUP.TXT" 2>&1
''')
    elif name=='f8-g3-assets/f8-official-report.timer':
        assert b'OnActiveSec=210s' in data;data=data.replace(b'OnActiveSec=210s',b'OnActiveSec=100s')
    elif name=='f8-g3-assets/graphics-run':
        data=(asset/'live-hardware.sh').read_bytes()
    elif name=='f8-g3-assets/power-readonly.py':
        data=(asset/'power-readonly.py').read_bytes()
    elif name=='f8-g3-assets/f8-official-graphics.service':
        data=data.replace(b'After=basic.target',b'After=f8-live-status.service basic.target')
    elif name=='f8-firstboot-logs.img':data=fat.read_bytes()
    if data!=body:changed.append(name)
    fields=list(values);fields[6]=len(data);new.append((name,fields,data))
template=next(v for n,v,b in records if n=='f8-g3-assets/touch-events.py')
def append(name,data,mode=0o100644):
    fields=list(template);fields[1]=mode;fields[6]=len(data);new.append((name,fields,data))
for name,data in payloads.items():append('f8-g3-assets/'+name,data)
fwinfo=json.loads((P/'analysis/armbian/wireless/verified-assets.json').read_text())
firmware=Path(fwinfo['staging_directory'])
append('f8-live-firmware',b'',0o40755)
for entry in fwinfo['files']:
    if not entry['path'].startswith('usr/lib/firmware/ap6275p/'):continue
    data=(firmware/entry['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==entry['sha256']
    append('f8-live-firmware/'+Path(entry['path']).name,data)
for name,target in fwinfo['relative_symlinks'].items():append('f8-live-firmware/'+name,target.encode(),0o120777)
packed=helper.cpio_write(new);check={n:b for n,_,b in helper.cpio_read(packed)}
assert len(check)==len(new),'No duplicate archive paths'
for name,_,body in records:
    if name not in changed:assert check[name]==body
# Execute the actual packed init asset-install loop, rather than assuming paths.
stage=work/'install-fixture';stage.mkdir(exist_ok=True)
staged_assets=stage/'assets';staged_assets.mkdir(exist_ok=True)
staged_root=stage/'root'
for directory in ['etc/systemd/system','usr/libexec/f8-pro']:(staged_root/directory).mkdir(parents=True,exist_ok=True)
for name,body in check.items():
    if name.startswith('f8-g3-assets/'): (staged_assets/Path(name).name).write_bytes(body)
inittext=check['init'].decode()
loop=inittext.split('for asset in /f8-g3-assets/*; do',1)[1].split('\ndone',1)[0]
loop='for asset in /f8-g3-assets/*; do'+loop+'\ndone\n'
loop=loop.replace('/f8-g3-assets/*',str(staged_assets)+'/*').replace('/mnt/root',str(staged_root))
install_script=stage/'install.sh';install_script.write_text('set -eu\nfail() { exit 1; }\n'+loop)
busybox=work/'busybox';busybox.write_bytes(check['bin/busybox']);busybox.chmod(0o755)
subprocess.run(['qemu-aarch64-static',str(busybox),'sh',str(install_script)],check=True)
assert (staged_root/'etc/systemd/system/f8-official-graphics.target').read_bytes()==payloads['f8-official-graphics.target']
assert not (staged_root/'usr/libexec/f8-pro/f8-official-graphics.target').exists()
assert b'systemctl start f8-official-wayland' not in check['f8-g3-assets/graphics-run']
for name,data in check.items():
    if name in ['init','f8-evaluation-report','f8-g3-assets/graphics-run'] or name.endswith('.sh'):
        path=work/(Path(name).name+'.check');path.write_bytes(data)
        subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(path)],check=True)
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
# Validate the final unit names together in a private overlay of the actual root.
unitwork=Path('/var/tmp/f8-pro-armbian/live-unit-check-v1')
for part in ['upper','work','root']:(unitwork/part).mkdir(parents=True,exist_ok=True)
verifyroot=unitwork/'root'
subprocess.run(['mount','-t','overlay','overlay','-o',f'lowerdir={root},upperdir={unitwork}/upper,workdir={unitwork}/work',str(verifyroot)],check=True)
try:
    units=[]
    for path,data in check.items():
        if path.startswith('f8-g3-assets/') and path.endswith(('.service','.target','.timer')):
            name=Path(path).name;dest=verifyroot/'etc/systemd/system'/name
            installed=staged_root/'etc/systemd/system'/name
            assert installed.read_bytes()==data
            dest.write_bytes(installed.read_bytes());units.append(name)
    result=subprocess.run(['systemd-analyze','--root='+str(verifyroot),'--man=no','verify',*units],capture_output=True,text=True)
    (out/'unit-verification.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr
finally:
    subprocess.run(['umount',str(verifyroot)],check=True)
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
its=Path('/var/tmp/f8-pro-armbian/official-power-g5/boot.its').read_text().replace('G5 PASSIVE POWER','G6 WIFI SSH LIVE')
(work/'boot.its').write_text(its)
candidate=out/'BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img'
(out/'mkimage.txt').write_text(subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(candidate)],cwd=work,text=True))
data=candidate.read_bytes();tree=fdt(data);hashes={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    value=data[a:a+size];assert value==(work/name).read_bytes()
    digest=hashlib.sha256(value).digest();assert digest==tree['/images/'+name+'/hash']['value'];hashes[name]=digest.hex()
assert len(data)<64*1024*1024
runtime=struct.unpack_from('<Q',(work/'kernel').read_bytes(),16)[0]
ranges=[(0x400000,0x400000+runtime),(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
        (0xa200000,0xa200000+(work/'ramdisk').stat().st_size)]
mem=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(x['base'],16),int(x['base'],16)+int(x['size'],16)) for x in mem['banks']]
for i,(a,b) in enumerate(ranges):
    assert any(x<=a<b<=y for x,y in banks)
    for j,(x,y) in enumerate(ranges):
        if i!=j:assert not(a<y and x<b)
report={'scope':'G6 r6 coherent ADC freshness and live SSH diagnostics; no charge-policy changes; boot trial pending',
 'candidate_file':candidate.name,'candidate_bytes':len(data),'candidate_sha256':hashlib.sha256(data).hexdigest(),
 'base_g5_sha256':prior['candidate_sha256'],'payload_sha256':hashes,'log_volume':'F8AG6',
 'wifi_gpio_pcie_phy_wiring_compared_to_factory':True,'private_data_in_boot_image':False,
 'private_profiles_keys_copied_only_from_readonly_arch_into_ram':True,'ssh_user':'f8test',
 'ssh_password_authentication':False,'charging_policy_register_writes':0,
 'adc_start_strobe_when_input_powered':True,'charger_driver_enabled':False,
 'power_poll_seconds':10,'report_timer_seconds':100,'wayland_window_seconds':0,
 'hardware_test_performed':False,'wifi_ssh_verified':False,'charging_validated':False,'deployment_performed':False}
report['busybox_existing_firmware_symlink_fix_verified_offline']=True
report['private_provisioning_deferred_until_systemd_basic']=True
report['provisioning_failure_does_not_abort_graphics_target']=True
report['actual_init_install_loop_verified']=True
report['automatic_popup_removed']=True
report['input_powered_adc_refresh_with_freshness_checks']=True
report['current_is_uncalibrated_estimate_not_actual_input_current']=True
report['adc_helpers_share_exclusive_lock']=True
report['sampling_component_verified_in_ram_under_r5']=True
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');(out/'live-g6.dtb').write_bytes((work/'fdt').read_bytes())
print(json.dumps(report,indent=2))
