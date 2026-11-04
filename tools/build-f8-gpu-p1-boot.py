"""Offline GPU-only 200/300/400 MHz trial, retaining R1a init and CPU guard."""
import copy,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
def sha(b):return hashlib.sha256(b).hexdigest()
def cells(*v):return struct.pack('>'+str(len(v))+'I',*v)
src=P/'outputs/armbian/f8-first-run-r1a/BOOT_ONLY_F8_ARMBIAN_R1A_SETUP_GROW.img'
b=src.read_bytes();assert sha(b)=='2a4901174382cbb8e0387f8de0220c8bebfff2fb830ca7d6aac5dd7794cb75dd'
O=P/'outputs/armbian/f8-gpu-p1';O.mkdir(exist_ok=True)
W=Path('/var/tmp/f8-pro-armbian/gpu-p1');W.mkdir(exist_ok=True)
target=O/'BOOT_ONLY_F8_ARMBIAN_GPU_P1.img'
assert not target.exists() and not (O/'preflight.json').exists(),'Never overwrite a candidate'
t=fdt(b);original={}
for n in ['kernel','ramdisk','fdt','resource']:
 q=t['/images/'+n];a=int.from_bytes(q['data-position'],'big');size=int.from_bytes(q['data-size'],'big')
 original[n]=b[a:a+size];assert hashlib.sha256(original[n]).digest()==t['/images/'+n+'/hash']['value']
 (W/n).write_bytes(original[n])
assert sha(original['kernel'])=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
d=fdt(original['fdt']);expected=copy.deepcopy(d);gpu='/gpu-panthor@fb000000';tz='/thermal-zones/gpu-thermal'
assert d[gpu]['status']==b'okay\0' and d['/gpu@fb000000']['status']==b'disabled\0'
args=d['/chosen']['bootargs'];assert b'cpufreq.off=1' in args and b'initcall_blacklist=rockchip_cpufreq_driver_init,rkcif_clr_unready_dev,rkisp_clr_unready_dev' in args
def put(p,k,v):
 subprocess.run(['fdtput','-t','bx',str(W/'fdt'),p,k,*[f'{x:02x}' for x in v]],check=True)
 expected[p][k]=v
def node(p):
 subprocess.run(['fdtput','-c',str(W/'fdt'),p],check=True);expected[p]={}
for rate in [300000000,400000000]:
 p=gpu+'/opp-table/opp-'+str(rate)
 assert d[p]['status']==b'disabled\0' and d[p]['opp-microvolt']==cells(675000,675000,850000)
 put(p,'status',b'okay\0')
# New passive trip and cooling map bind to Panthor's existing #cooling-cells.
ph=max(int.from_bytes(v['phandle'],'big') for v in d.values() if 'phandle' in v)+1
trip=tz+'/trips/gpu-passive-p1';node(trip)
for k,v in {'temperature':cells(80000),'hysteresis':cells(5000),'type':b'passive\0','phandle':cells(ph)}.items():put(trip,k,v)
maps=tz+'/cooling-maps'
if maps not in expected:node(maps)
mapping=maps+'/gpu-p1';node(mapping)
put(mapping,'trip',cells(ph));put(mapping,'cooling-device',d[gpu]['phandle']+cells(0xffffffff,0xffffffff))
put('/chosen','f8-gpu-trial',b'p1-400mhz\0')
dt=(W/'fdt').read_bytes();assert fdt(dt)==expected
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(W/'resource').write_bytes(replace_dtb(original['resource'],dt))
assert parse((W/'resource').read_bytes())['rk-kernel.dtb']==dt
(W/'boot.its').write_bytes((P/'armbian/camera/boot-c4.its').read_bytes())
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=W,check=True,stdout=subprocess.DEVNULL,env=dict(os.environ,SOURCE_DATE_EPOCH=str(int.from_bytes(t['/']['timestamp'],'big'))))
final=target.read_bytes();ft=fdt(final)
assert set(ft)==set(t)
for p,props in ft.items():
 assert set(props)==set(t[p])
 for k,v in props.items():
  if p.startswith('/images/') and k in {'data-position','data-size','value'}:continue
  assert v==t[p][k],(p,k)
for n in original:
 q=ft['/images/'+n];a=int.from_bytes(q['data-position'],'big');size=int.from_bytes(q['data-size'],'big');body=final[a:a+size]
 assert body==(W/n).read_bytes() and hashlib.sha256(body).digest()==ft['/images/'+n+'/hash']['value']
 if n in {'kernel','ramdisk'}:assert body==original[n]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
 size=(W/name).stat().st_size+slack
 assert any(int(x['base'],16)<=address and address+size<=int(x['base'],16)+int(x['size'],16) for x in memory['banks'])
assert len(final)<64*1024**2
report={'file':target.name,'bytes':len(final),'sha256':sha(final),'boot_lba':'0x00008000','base':'R1a','kernel_ramdisk_byte_identical':True,'kernel_sha256':sha(original['kernel']),'cpu_bootargs_unchanged':True,'gpu_enabled_rates_hz':[200000000,300000000,400000000],'gpu_opp_voltage_unchanged':True,'gpu_target_voltage_uv':675000,'gpu_passive_trip_celsius':80,'fit_resource_memory_capacity_verified':True,'device_written':False,'cold_boot_verified':False,'performance_improvement_measured':False,'rollback_file':str(src.relative_to(P)),'rollback_sha256':sha(b),'rootfs_reflash_required':False}
(O/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'SHA256SUMS').write_text(sha(final)+'  '+target.name+'\n')
print(json.dumps(report,indent=2))
