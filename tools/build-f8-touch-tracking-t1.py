"""Build T1 with one algorithm setting change; preserve the known-good module."""
import argparse,ast,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'armbian/touch/official-6.1.115-f8'
parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=['t1','t2'],default='t1');args=parser.parse_args()
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
G=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
W=Path('/var/tmp/f8-pro-armbian/f8-touch-tracking-'+args.profile);W.mkdir(exist_ok=True)
O=P/('outputs/armbian/f8-touch-tracking-'+args.profile);O.mkdir(parents=True,exist_ok=True)
assert not (O/'module-check.json').exists(),'Preserve completed build'
old=S/'f8_gsl_shuping.ko';assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
for name in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:
 shutil.copyfile(S/name,W/name)
header=W/'f8-pro-r8-shuping-reference.h';h=header.read_text();before,body=h.split('static unsigned int f8_pro_r8_shuping_algorithm[] = {',1)
matches=list(re.finditer(r'0x[0-9a-fA-F]+',body.split('};',1)[0]));assert len(matches)==512 and int(matches[0x18][0],16)==0
edits={0x18:'0x00100018'}
if args.profile=='t2':
 assert int(matches[0x28][0],16)==0x1b6db688
 edits[0x28]='0x09249248' # Keep single=0 and double=1; 3+ contacts wait one frame.
for i,value in sorted(edits.items(),reverse=True):
 m=matches[i];body=body[:m.start()]+value+body[m.end():]
header.write_text(before+'static unsigned int f8_pro_r8_shuping_algorithm[] = {'+body)
(W/'Makefile').write_text('obj-m := f8_gsl_shuping.o\nf8_gsl_shuping-y := f8_gsl_driver.o gsl_point_id.o\nccflags-y += -I'+str(G)+'\n')
with (O/'build.log').open('w') as f:
 r=subprocess.run(['make','-C',str(H),'M='+str(W),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,(O/'build.log').read_text()[-3000:]
syntax=ast.parse((P/'tools/build-f8-official-touch-module.py').read_text())
exec(compile(ast.Module(body=[n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name in ['elf_sections','versions']],type_ignores=[]),'abi-helpers','exec'))
new=W/'f8_gsl_shuping.ko';assert versions(new.read_bytes())==versions(old.read_bytes()),'Imported ABI differs from actual-verified baseline'
magic=subprocess.check_output(['modinfo','-F','vermagic',str(new)],text=True).strip();assert magic==subprocess.check_output(['modinfo','-F','vermagic',str(old)],text=True).strip()
def array(file,name,section):
 data=file.read_bytes();sections=elf_sections(data);symbols=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(file)],text=True)
 line=next(l for l in symbols.splitlines() if l.endswith(' '+name));fields=line.split();offset,size=[int(v,16) for v in fields[:2]];s=sections[section];return data[s[4]+offset:s[4]+offset+size]
firmware=array(new,'f8_pro_r8_shuping_fw','.rodata');assert firmware==array(old,'f8_pro_r8_shuping_fw','.rodata')
oldconf=struct.unpack('<512I',array(old,'f8_pro_r8_shuping_algorithm','.data'));newconf=struct.unpack('<512I',array(new,'f8_pro_r8_shuping_algorithm','.data'))
assert [i for i,(x,y) in enumerate(zip(oldconf,newconf)) if x!=y]==sorted(edits) and newconf[0x18]==0x00100018
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(new)],check=True)
shutil.copyfile(new,O/new.name)
for name in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:shutil.copyfile(W/name,O/name)
report={'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'bytes':new.stat().st_size,'vermagic':magic,'import_crcs_identical_to_actual_verified_baseline':True,'firmware_identical':True,'driver_and_algorithm_source_unchanged':True,'algorithm_config_changed_index':'0x18','old':hex(oldconf[0x18]),'new':hex(newconf[0x18]),'repeat_thresholds':[16,24],'baseline_fallback_thresholds':[32,96],'hardware_loaded':False,'reboot_persistence_tested':False}
report.update(profile=args.profile,algorithm_config_changes={hex(i):{'old':hex(oldconf[i]),'new':hex(newconf[i])} for i in edits},report_delay_by_count=[(newconf[0x28]>>(3*n))&7 for n in range(10)])
(O/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
