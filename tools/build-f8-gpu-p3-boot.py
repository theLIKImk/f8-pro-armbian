"""P2A CPU core plus full GPU OPP table; root service gates initial GPU cap."""
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
def sha(b):return hashlib.sha256(b).hexdigest()
src=P/'outputs/armbian/f8-cpu-p2a/BOOT_ONLY_F8_ARMBIAN_CPU_P2A.img';b=src.read_bytes()
assert sha(b)=='a3a23fd7ea637cff25e333f7c52d212a9a9310f8b3ebb0b54a25a700301aa76e'
O=P/'outputs/armbian/f8-gpu-p3';O.mkdir(exist_ok=True)
W=Path('/var/tmp/f8-pro-armbian/gpu-p3-boot');W.mkdir(exist_ok=True)
target=O/'BOOT_ONLY_F8_ARMBIAN_FULL_PERF_P3.img';assert not target.exists() and not (O/'preflight.json').exists()
t=fdt(b);original={}
for n in ['kernel','ramdisk','fdt','resource']:
 q=t['/images/'+n];a=int.from_bytes(q['data-position'],'big');size=int.from_bytes(q['data-size'],'big')
 original[n]=b[a:a+size];assert hashlib.sha256(original[n]).digest()==t['/images/'+n+'/hash']['value'];(W/n).write_bytes(original[n])
d=fdt(original['fdt']);expected=copy.deepcopy(d)
def put(p,k,v):
 subprocess.run(['fdtput','-t','bx',str(W/'fdt'),p,k,*[f'{x:02x}' for x in v]],check=True);expected[p][k]=v
enabled=[]
for mhz in [500,600,700,800,900,1000]:
 p='/gpu-panthor@fb000000/opp-table/opp-'+str(mhz*1000000)
 assert d[p]['status']==b'disabled\0'
 uv=[int.from_bytes(d[p]['opp-microvolt'][i:i+4],'big') for i in range(0,len(d[p]['opp-microvolt']),4)]
 assert len(uv)==3 and uv[0]<=850000 and uv[2]<=850000
 put(p,'status',b'okay\0');enabled.append({'mhz':mhz,'microvolts':uv})
put('/chosen','f8-gpu-trial',b'p3-1000mhz\0')
dt=(W/'fdt').read_bytes();assert fdt(dt)==expected
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(W/'resource').write_bytes(replace_dtb(original['resource'],dt));assert parse((W/'resource').read_bytes())['rk-kernel.dtb']==dt
(W/'boot.its').write_bytes((P/'armbian/camera/boot-c4.its').read_bytes())
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=W,check=True,stdout=subprocess.DEVNULL,env=dict(os.environ,SOURCE_DATE_EPOCH=str(int.from_bytes(t['/']['timestamp'],'big'))))
final=target.read_bytes();ft=fdt(final);assert set(ft)==set(t)
for p,props in ft.items():
 assert set(props)==set(t[p])
 for k,v in props.items():
  if p.startswith('/images/') and k in {'data-position','data-size','value'}:continue
  assert v==t[p][k],(p,k)
for n in original:
 q=ft['/images/'+n];a=int.from_bytes(q['data-position'],'big');size=int.from_bytes(q['data-size'],'big');body=final[a:a+size]
 assert body==(W/n).read_bytes() and hashlib.sha256(body).digest()==ft['/images/'+n+'/hash']['value']
 if n in {'kernel','ramdisk'}:assert body==original[n]
assert expected['/chosen']['bootargs']==d['/chosen']['bootargs']
assert expected['/chosen']['f8-cpu-trial']==b'p2-fixedvolt-1200mhz\0'
assert len(final)<64*1024**2
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
 size=(W/name).stat().st_size+slack
 assert any(int(x['base'],16)<=address and address+size<=int(x['base'],16)+int(x['size'],16) for x in memory['banks'])
out={'file':target.name,'bytes':len(final),'sha256':sha(final),'boot_lba':'0x00008000','base':'CPU P2A','kernel_ramdisk_cpu_args_identical_to_P2A':True,'new_gpu_opps':enabled,'gpu_thermal_configuration_unchanged':True,'initial_gpu_cap_requires_root_service':True,'first_boot_gpu_certified_cap_mhz':400,'deferred_cpu_full_driver_requires_root_assets':True,'fit_resource_memory_capacity_verified':True,'cold_boot_verified':False,'device_written':False,'rollback_file':str(src.relative_to(P)),'rollback_sha256':sha(b)}
(O/'preflight.json').write_text(json.dumps(out,indent=2)+'\n');(O/'SHA256SUMS').write_text(sha(final)+'  '+target.name+'\n');print(json.dumps(out,indent=2))
