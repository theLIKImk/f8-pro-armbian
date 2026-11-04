"""Restore board camera resources and factory graphs on the verified S1 base."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-motion-s1';prior=json.loads((base/'preflight.json').read_text())
assert prior['cold_boot_verified'] and prior['autorotation_verified']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-camera-c1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/camera-c1');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
before=fdt(original['fdt']);expected=copy.deepcopy(before)
factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
old_handles={int.from_bytes(v['phandle'],'big'):p for p,v in factory.items() if 'phandle' in v}
new_handles={p:int.from_bytes(v['phandle'],'big') for p,v in expected.items() if 'phandle' in v}
next_handle=max(new_handles.values())+1
changed=[]
def cell(n):return n.to_bytes(4,'big')
def cells(value):return [int.from_bytes(value[i:i+4],'big') for i in range(0,len(value),4)]
def ensure(path):
    if path in expected:return
    parent=path.rsplit('/',1)[0] or '/';ensure(parent)
    subprocess.run(['fdtput','-c',str(work/'fdt'),path],check=True);expected[path]={}
def put(path,name,value):
    ensure(path)
    if expected[path].get(name)==value:return
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),path,name,*[f'{n:02x}' for n in value]],check=True)
    expected[path][name]=value;changed.append([path,name])
def handle(path):
    global next_handle
    if path not in new_handles:
        new_handles[path]=next_handle;next_handle+=1;put(path,'phandle',cell(new_handles[path]))
    return new_handles[path]
def map_ref(n):
    path=old_handles[n]
    assert path in expected or path in clone_paths,(path,'missing reference provider')
    return handle(path)
bus='/i2c@fead0000'
sensor_roots=[bus+'/gc5035@37',bus+'/ov8858@36',bus+'/dw9714@c']
routes=['/csi2-dphy1','/csi2-dphy2','/mipi2-csi2','/mipi3-csi2',
 '/rkcif-mipi-lvds2','/rkcif-mipi-lvds3','/rkcif-mipi-lvds2-sditf','/rkcif-mipi-lvds3-sditf',
 '/rkisp0-vir0','/rkisp1-vir0']
clone_paths={p for p in factory if any(p==r or p.startswith(r+'/') for r in sensor_roots)}
clone_paths|={p for p in factory if any(p.startswith(r+'/') for r in routes)}
# Restore only board-level pin groups and the original camera power gate.
pin_roots=['/pinctrl/i2c5/i2c5m3-xfer','/pinctrl/mipi/mipim1-camera1-clk','/pinctrl/cam/mipidcphy-pwr']
clone_paths.update(pin_roots);clone_paths.add('/vcc-mipidcphy-regulator')
for path in sorted(clone_paths,key=lambda p:(p.count('/'),p)):ensure(path)
for path in clone_paths:
    if 'phandle' in factory[path]:handle(path)
first_ref=['clocks','power-domains','rockchip,grf','reset-gpios','pwdn-gpios','power-gpios','gpio','avdd-supply','vin-supply','remote-endpoint','lens-focus']
for path in sorted(clone_paths):
    for name,value in factory[path].items():
        if name=='phandle':continue
        if name=='flash-leds':continue # Flash adaptation intentionally separate.
        if name in first_ref:
            n=cells(value);n[0]=map_ref(n[0]);value=b''.join(cell(i) for i in n)
        elif name.startswith('pinctrl-') and name!='pinctrl-names':value=b''.join(cell(map_ref(n)) for n in cells(value))
        elif name=='rockchip,pins':
            n=cells(value)
            for i in range(3,len(n),4):n[i]=map_ref(n[i])
            value=b''.join(cell(i) for i in n)
        put(path,name,value)
put(bus,'pinctrl-0',cell(handle(pin_roots[0])));put(bus,'status',b'okay\0')
hardware=['/rkcif@fdce0000','/rkisp@fdcb0000','/rkisp@fdcc0000']
for path in routes+hardware:
    assert path in before,path
    assert before[path]['status']==b'disabled\0',path
    put(path,'status',b'okay\0')
for path in hardware:
    ph=before[path]['iommus'][:4]
    iommu=next(p for p,v in before.items() if v.get('phandle')==ph)
    assert iommu.startswith('/iommu@');put(iommu,'status',b'okay\0')
put('/chosen','f8-camera-trial',b'c1\0')
dt=(work/'fdt').read_bytes();after=fdt(dt);assert after==expected
# Check every restored endpoint is reciprocal and both sensors stay on 2 lanes.
reverse={int.from_bytes(v['phandle'],'big'):p for p,v in after.items() if 'phandle' in v}
links=[]
for path in clone_paths:
    if 'remote-endpoint' in after[path]:
        other=reverse[int.from_bytes(after[path]['remote-endpoint'],'big')]
        assert after[other]['remote-endpoint']==after[path]['phandle'],(path,other)
        links.append([path,other])
assert len(links)==16,len(links)
for path in sensor_roots[:2]:
    assert after[path+'/port/endpoint']['data-lanes']==cell(1)+cell(2)
    assert after[path]['avdd-supply']==cell(handle('/vcc-mipidcphy-regulator'))
assert after['/chosen']['bootargs']==before['/chosen']['bootargs']
for prop,value in [('f8-usb-trial',b'u5\0'),('f8-bluetooth-trial',b'bt1\0'),('f8-motion-trial',b's1\0')]:assert after['/chosen'][prop]==value
phy='/syscon@fd5d0000/usb2-phy@0'
assert [p for p in after if p.rsplit('/',1)[0]==phy]==[p for p in before if p.rsplit('/',1)[0]==phy]
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/motion-s1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_CAMERA_C1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();tree=fdt(data)
for name in original:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');body=data[a:a+n]
    assert body==(work/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    if name in ['kernel','ramdisk']:assert body==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'base':'verified S1 plus existing native-root runtime fixes','sensors':['GC5035 front 5-0037','OV8858 back 5-0036'],
 'i2c5_factory_m3_restored':True,'camera_power_original_gpio_1_4_and_DCDC8':True,'graph_reciprocal_endpoints_checked':len(links),
 'all_copied_phandles_translated_by_path':True,'graph_links':links,'changed_properties':changed,
 'soc_hardware_clocks_resets_domains_preserved':True,'kernel_ramdisk_cmdline_preserved':True,
 'fit_resource_sync_hashes_memory_capacity_verified':True,'existing_usb_bluetooth_motion_profiles_preserved':True,
 'rootfs_reflash_required':False,'cold_boot_verified':False,'sensor_identity_verified':False,'frame_capture_verified':False,
 'isp_3a_verified':False,'autofocus_verified':False,'flash_enabled':False,'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['graph_links','changed_properties']},indent=2))
