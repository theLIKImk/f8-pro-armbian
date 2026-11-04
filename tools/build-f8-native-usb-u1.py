"""BOOT-only Type-C/USB2 OTG trial on verified A3; no device writes."""
import copy,gzip,hashlib,importlib.util,json,stat,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-native-audio-a3';prior=json.loads((base/'preflight.json').read_text())
assert prior['cold_boot_verified'] and prior['audio_playback_verified']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
modulebase=P/'outputs/armbian/official-f8-usb-u1-module';meta=json.loads((modulebase/'module-check.json').read_text())
assert meta['all_import_crcs_match_actual_official_kernel']
module=(modulebase/meta['module']).read_bytes();assert hashlib.sha256(module).hexdigest()==meta['sha256']
pre=json.loads((P/'local/hardware/armbian-native-usb-20261101/prerequisites01.json').read_text())
claims='\n'.join(s for lines in pre['pinmux'].values() for s in lines)
for pin in [20,134]:assert f'pin {pin} ' in claims
assert all('(MUX UNCLAIMED) (GPIO UNCLAIMED)' in s for lines in pre['pinmux'].values() for s in lines)
out=P/'outputs/armbian/official-f8-native-usb-u1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-usb-u1');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];a=int.from_bytes(props['data-position'],'big');n=int.from_bytes(props['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
assert b'fcs,int_n' in original['kernel'],'Confirm GPIO property name in actual built-in driver'
before=fdt(original['fdt']);expected=copy.deepcopy(before)
refs={v['phandle']:k for k,v in before.items() if 'phandle' in v}
next_handle=max(int.from_bytes(v['phandle'],'big') for v in before.values() if 'phandle' in v)+1
def cells(*values):return struct.pack('>'+str(len(values))+'I',*values)
def node(path):
    if path in expected:return
    parent=path.rsplit('/',1)[0] or '/'
    node(parent)
    subprocess.run(['fdtput','-c',str(work/'fdt'),path],check=True);expected[path]={}
def prop(path,key,value):
    node(path)
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),path,key,*[f'{b:02x}' for b in value]],check=True)
    expected[path][key]=value
def text(path,key,value):prop(path,key,value.encode()+b'\0')
def handle(path):
    global next_handle
    if 'phandle' not in expected.get(path,{}):
        prop(path,'phandle',cells(next_handle));next_handle+=1
    return expected[path]['phandle']
gpio0=next(p for p,v in before.items() if p.endswith('/gpio@fd8a0000'))
gpio4=next(p for p,v in before.items() if p.endswith('/gpio@fec50000'))
pullup=next(p for p,v in before.items() if p.startswith('/pinctrl/') and v.get('bias-pull-up')==b'' and 'phandle' in v and len(set(v)-{'phandle','bias-pull-up','input-enable'})==0)
group='/pinctrl/f8-usb-u1/typec-irq'
prop(group,'rockchip,pins',cells(0,20,0)+before[pullup]['phandle'])
i2c='/i2c@fec80000';charger=i2c+'/charger@6a';tcpc=i2c+'/fusb302@22';reg=charger+'/regulators/usb-otg-vbus'
assert before[charger]['status']==b'disabled\0'
assert refs[before[charger]['otg-mode-en-gpios'][:4]]==gpio4
assert before[charger]['otg-mode-en-gpios'][4:]==cells(6,0)
text(charger,'compatible','f8-pro,otg-vbus-only');text(charger,'status','okay')
text(reg,'regulator-name','f8_usb_otg_vbus');prop(reg,'regulator-min-microvolt',cells(5000000));prop(reg,'regulator-max-microvolt',cells(5000000));handle(reg)
text(tcpc,'compatible','fcs,fusb302');prop(tcpc,'reg',cells(0x22));text(tcpc,'status','okay')
text(tcpc,'pinctrl-names','default');prop(tcpc,'pinctrl-0',handle(group))
prop(tcpc,'fcs,int_n-gpios',before[gpio0]['phandle']+cells(20,1))
prop(tcpc,'interrupt-parent',before[gpio0]['phandle']);prop(tcpc,'interrupts',cells(20,8))
prop(tcpc,'vbus-supply',handle(reg))
connector=tcpc+'/connector'
for key,value in [('compatible','usb-c-connector'),('label','F8 USB-C'),('data-role','dual'),('power-role','dual'),('try-power-role','sink')]:text(connector,key,value)
pdo=(1<<29)|(1<<26)|(1<<25)|(100<<10)|50
prop(connector,'source-pdos',cells(pdo));prop(connector,'sink-pdos',cells(pdo));prop(connector,'op-sink-microwatt',cells(2500000))
usb='/usbdrd3_0/usb@fc000000'
text(usb,'dr_mode','otg');prop(usb,'usb-role-switch',b'');text(usb,'role-switch-default-mode','peripheral')
endpoint=usb+'/port/endpoint';peer=connector+'/ports/port@0/endpoint'
prop(connector+'/ports','#address-cells',cells(1));prop(connector+'/ports','#size-cells',cells(0))
prop(connector+'/ports/port@0','reg',cells(0))
prop(endpoint,'remote-endpoint',handle(peer));prop(peer,'remote-endpoint',handle(endpoint))
chosen='/chosen';args=before[chosen]['bootargs'].rstrip(b'\0');assert b'f8_usb_u1=' not in args
prop(chosen,'bootargs',args+b' f8_usb_u1=1\0')
assert fdt((work/'fdt').read_bytes())==expected
assert expected['/pwm@febf0020']==before['/pwm@febf0020']
assert expected['/i2c@fec90000/es8388@11']==before['/i2c@fec90000/es8388@11']
assert len((work/'fdt').read_bytes())<len(original['fdt'])+8192
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');cpio=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpio)
records=cpio.cpio_read(gzip.decompress(original['ramdisk']))
dropin=b'[Unit]\nConditionKernelCommandLine=!f8_usb_u1=1\n'
digest=hashlib.sha256(dropin).hexdigest()
patch=f'''# U1: kernel owns OTG; skip userspace ADC while this trial is selected.
pause=/mnt/root/etc/systemd/system/f8-live-power.service.d/98-f8-usb-u1.conf
mkdir -p /mnt/root/etc/systemd/system/f8-live-power.service.d || fail usb-power-directory
if [ -e "$pause" ]; then
    [ ! -L "$pause" ] || fail usb-power-symlink
    case "$(sha256sum "$pause")" in '{digest} '*) ;; *) fail usb-power-unexpected;; esac
else
    cp /f8-usb-u1-power.conf "$pause" || fail usb-power-install
    chmod 0644 "$pause" || fail usb-power-mode
fi
insmod /f8_otg_vbus.ko || fail usb-otg-module
echo 'U1 USB2 OTG trial: narrow VBUS driver loaded, power sampler skipped'
'''.encode()
new=[]
for name,values,body in records:
    if name=='init':
        anchor=b'moved=\n';assert body.count(anchor)==1;body=body.replace(anchor,patch+anchor)
    v=list(values);v[6]=len(body);new.append((name,v,body))
for ino,(name,body) in enumerate([('f8_otg_vbus.ko',module),('f8-usb-u1-power.conf',dropin)],200101):
    new.append((name,[ino,stat.S_IFREG|0o644,0,0,1,0,len(body),0,0,0,0,0,0],body))
packed=cpio.cpio_write(new);checked={n:b for n,v,b in cpio.cpio_read(packed)}
assert checked['f8_otg_vbus.ko']==module
busy=work/'busybox';busy.write_bytes(checked['bin/busybox']);busy.chmod(0o755)
(work/'init.sh').write_bytes(checked['init'])
subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(work/'init.sh')],check=True)
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-audio-a3/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();tree=fdt(data)
for name in original:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');body=data[a:a+n]
    assert body==(work/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    if name in ['kernel','resource']:assert body==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
changes=[[p,k] for p,v in before.items() for k in v if expected[p].get(k)!=v[k]]
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'base':'A3 verified speaker/backlight','changed_existing_dt_properties':changes,'added_dt_nodes':sorted(set(expected)-set(before)),'module_sha256':meta['sha256'],'module_abi_checked_against_actual_kernel':True,'usb2_only':True,'source_and_sink_pdo':'5V 500mA only','charger_initialization':False,'otg_control_writes':'Only REG03 OTG_CONFIG and board GPIO4_A6; no hardware writes during build','power_sampler_paused_only_with_u1_boot_argument':True,'a3_rollback_resumes_power_sampler':True,'kernel_resource_unchanged':True,'audio_backlight_preserved':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
