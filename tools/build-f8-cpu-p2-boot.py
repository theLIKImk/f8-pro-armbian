"""P1 with CPU core enabled but vendor/DT autoprobes blocked; manual P2 only."""
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
def sha(b):return hashlib.sha256(b).hexdigest()
src=P/'outputs/armbian/f8-gpu-p1/BOOT_ONLY_F8_ARMBIAN_GPU_P1.img'
b=src.read_bytes();assert sha(b)=='aaabb0ff25cbc339f6a233a0fed5939fd96c228328b315a0039f66e546b5d7b3'
O=P/'outputs/armbian/f8-cpu-p2a';O.mkdir(exist_ok=True)
W=Path('/var/tmp/f8-pro-armbian/cpu-p2a-boot');W.mkdir(exist_ok=True)
target=O/'BOOT_ONLY_F8_ARMBIAN_CPU_P2A.img';assert not target.exists() and not (O/'preflight.json').exists()
module=json.loads((O/'module-check.json').read_text());assert module['actual_image_import_crcs_verified'] and not module['automatic_loading']
t=fdt(b);original={}
for n in ['kernel','ramdisk','fdt','resource']:
 q=t['/images/'+n];a=int.from_bytes(q['data-position'],'big');size=int.from_bytes(q['data-size'],'big')
 original[n]=b[a:a+size];assert hashlib.sha256(original[n]).digest()==t['/images/'+n+'/hash']['value'];(W/n).write_bytes(original[n])
assert sha(original['kernel'])=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
d=fdt(original['fdt']);expected=copy.deepcopy(d);old=d['/chosen']['bootargs'].rstrip(b'\0').decode()
assert old.split().count('cpufreq.off=1')==1 and 'cpufreq.default_governor=' not in old
black='initcall_blacklist=rockchip_cpufreq_driver_init,rkcif_clr_unready_dev,rkisp_clr_unready_dev';assert old.count(black)==1
new=old.replace('cpufreq.off=1','cpufreq.default_governor=powersave').replace(black,black+',cpufreq_dt_platdev_init')
for key,value in {'bootargs':new.encode()+b'\0','f8-cpu-trial':b'p2-fixedvolt-1200mhz\0'}.items():
 subprocess.run(['fdtput','-t','bx',str(W/'fdt'),'/chosen',key,*[f'{x:02x}' for x in value]],check=True);expected['/chosen'][key]=value
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
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
 size=(W/name).stat().st_size+slack
 assert any(int(x['base'],16)<=address and address+size<=int(x['base'],16)+int(x['size'],16) for x in memory['banks'])
assert len(final)<64*1024**2
out={'file':target.name,'bytes':len(final),'sha256':sha(final),'boot_lba':'0x00008000','base':'GPU P1','kernel_ramdisk_identical_to_P1':True,'dt_changes_only':['/chosen/bootargs','/chosen/f8-cpu-trial'],'old_cmdline':old,'new_cmdline':new,'vendor_cpu_initializer_still_blacklisted':True,'generic_dt_platform_initializer_also_blacklisted':True,'cpu_default_governor':'powersave','cpu_driver_in_ramdisk':False,'manual_module_required':True,'module_sha256':module['module_sha256'],'voltage_properties_unchanged':True,'gpu_p1_unchanged':True,'fit_resource_memory_capacity_verified':True,'cold_boot_verified':False,'device_written':False,'rollback_file':str(src.relative_to(P)),'rollback_sha256':sha(b),'rootfs_reflash_required':False}
(O/'preflight.json').write_text(json.dumps(out,indent=2)+'\n');(O/'SHA256SUMS').write_text(sha(final)+'  '+target.name+'\n');print(json.dumps(out,indent=2))
