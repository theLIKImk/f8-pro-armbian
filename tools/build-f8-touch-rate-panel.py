"""One parameterized timing module, verified against the actual kernel exports."""
import ast,hashlib,json,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'armbian/touch/official-6.1.115-f8'
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
G=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
W=Path('/var/tmp/f8-pro-armbian/f8-touch-rate-panel-r1');W.mkdir(exist_ok=True)
O=P/'outputs/armbian/f8-touch-rate-panel-r1';O.mkdir(parents=True,exist_ok=True)
assert not (O/'module-check.json').exists(),'Preserve completed build'
for name in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:shutil.copyfile(S/name,W/name)
header=W/'f8-pro-r8-shuping-reference.h';text=header.read_text()
assert text.count('static const struct fw_data f8_pro_r8_shuping_fw[]')==1
header.write_text(text.replace('static const struct fw_data f8_pro_r8_shuping_fw[]','static struct fw_data f8_pro_r8_shuping_fw[]'))
source=W/'f8_gsl_driver.c';text=source.read_text()
params='''
/* Parameters only apply during insertion. The existing PM/init path reuses the
 * patched SRAM image; the persistent boot module remains untouched. */
static unsigned int f8_rate_period = 280;
static unsigned long f8_rate_irqs, f8_rate_reads;
module_param_named(period, f8_rate_period, uint, 0444);
module_param_named(irq_count, f8_rate_irqs, ulong, 0444);
module_param_named(read_count, f8_rate_reads, ulong, 0444);
MODULE_PARM_DESC(period, "F8 acquisition timing, 122..320; not literal Hz");
static int f8_rate_prepare(void)
{
 u32 page=0, sum=0, addr;size_t i;bool timing=false,check=false;
 if(f8_rate_period<122 || f8_rate_period>320)return -EINVAL;
 for(i=0;i<ARRAY_SIZE(f8_pro_r8_shuping_fw);i++) {
  struct fw_data *w=&f8_pro_r8_shuping_fw[i];
  if(w->offset==0xf0){page=w->val;continue;}
  addr=page*128+w->offset;
  if(addr==0x374){if(w->val!=280)return -EINVAL;w->val=f8_rate_period;timing=true;}
  if(addr==0x180){if(w->val!=0x40bce5ce)return -EINVAL;w->val+=280-f8_rate_period;check=true;}
 }
 if(!timing || !check)return -EINVAL;
 page=0;
 for(i=0;i<ARRAY_SIZE(f8_pro_r8_shuping_fw);i++) {
  struct fw_data *w=&f8_pro_r8_shuping_fw[i];
  if(w->offset==0xf0){page=w->val;continue;}
  addr=page*128+w->offset;
  if((addr<0x500 || (addr>=0xd00 && addr<0x50b8)) && addr!=0x1fc && addr!=0x200)sum+=w->val;
 }
 return sum==0x5a5a5a5a?0:-EINVAL;
}
'''
anchor='#include "f8-pro-r8-shuping-reference.h"';assert text.count(anchor)==1;text=text.replace(anchor,anchor+'\n'+params)
anchor='\tts_irq_disable(ts);\n\tif (!work_pending(&ts->work))';assert text.count(anchor)==1
text=text.replace(anchor,'\tWRITE_ONCE(f8_rate_irqs, READ_ONCE(f8_rate_irqs) + 1);\n'+anchor)
anchor='\ttouches = ts->touch_data[ts->dd->touch_index];';assert text.count(anchor)==1
text=text.replace(anchor,'\tWRITE_ONCE(f8_rate_reads, READ_ONCE(f8_rate_reads) + 1);\n'+anchor)
anchor='static int __init gsl_ts_init(void)\n{\n\treturn i2c_add_driver(&gsl_ts_driver);\n}'
assert text.count(anchor)==1
text=text.replace(anchor,'static int __init gsl_ts_init(void)\n{\n\tint ret = f8_rate_prepare();\n\tif (ret) return ret;\n\treturn i2c_add_driver(&gsl_ts_driver);\n}')
source.write_text(text)
(W/'Makefile').write_text('obj-m := f8_gsl_shuping.o\nf8_gsl_shuping-y := f8_gsl_driver.o gsl_point_id.o\nccflags-y += -I'+str(G)+'\n')
with (O/'build.log').open('w') as log:r=subprocess.run(['make','-C',str(H),'M='+str(W),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(O/'build.log').read_text()[-4000:]
tree=ast.parse((P/'tools/build-f8-motion-iio.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='versions'],type_ignores=[]),'elf-parser','exec'))
module=W/'f8_gsl_shuping.ko';required=versions(module.read_bytes())
symbols={a[2]:int(a[0],16) for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines() if len(a:=line.split())==3}
kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes();assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
exports={};base=symbols['_text']
for suffix in ['', '_gpl']:
 start,end=symbols['__start___ksymtab'+suffix],symbols['__stop___ksymtab'+suffix];cs,ce=symbols['__start___kcrctab'+suffix],symbols['__stop___kcrctab'+suffix]
 assert (end-start)//12==(ce-cs)//4
 for name,entry in symbols.items():
  if name.startswith('__ksymtab_') and start<=entry<end:exports[name[10:]]=struct.unpack_from('<I',kernel,cs-base+(entry-start)//12*4)[0]
for name,crc in required.items():assert exports.get(name)==crc,(name,crc,exports.get(name))
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip();assert magic=='6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64'
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True)
shutil.copyfile(module,O/'f8_gsl_rate.ko')
for n in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:shutil.copyfile(W/n,O/n)
report={'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'srcversion':subprocess.check_output(['modinfo','-F','srcversion',str(module)],text=True).strip(),'vermagic':magic,'all_import_crcs_verified_against_actual_image':True,'imports':required,'period_range':[122,320],'default_period':280,'algorithm_config_unchanged':True,'rate_counters':True,'firmware_checksum_checked_at_insertion':True,'persistent_module_replaced':False}
(O/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
