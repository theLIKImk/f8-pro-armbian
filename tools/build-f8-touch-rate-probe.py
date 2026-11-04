"""Offline, reversible acquisition-timing probe; NOT a verified 120Hz profile."""
import argparse,ast,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'armbian/touch/official-6.1.115-f8'
p=argparse.ArgumentParser();p.add_argument('--period',type=int,choices=[252,157,128,122],default=252);args=p.parse_args()
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
G=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
label='f8-touch-rate-p'+str(args.period);W=Path('/var/tmp/f8-pro-armbian')/label;W.mkdir(exist_ok=True)
O=P/'outputs/armbian'/label;O.mkdir(parents=True,exist_ok=True);assert not (O/'module-check.json').exists()
old=S/'f8_gsl_shuping.ko';assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
for name in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:shutil.copyfile(S/name,W/name)
header=W/'f8-pro-r8-shuping-reference.h';text=header.read_text();before,rest=text.split('static const struct fw_data f8_pro_r8_shuping_fw[] = {',1);body,after=rest.split('};',1)
entries=list(re.finditer(r'\{\s*(0x[0-9a-fA-F]+)\s*,\s*(0x[0-9a-fA-F]+)\s*\}',body))
words={};locations={};page=None
for entry in entries:
 offset,value=[int(x,16) for x in entry.groups()]
 if offset==0xf0:page=value
 else:words[page*128+offset]=value;locations[page*128+offset]=entry.span(2)
def checksum(w):return (sum(w[a] for a in [*range(0,0x500,4),*range(0xd00,w[0xff8],4)])-w[0x1fc]-w[0x200])&0xffffffff
assert checksum(words)==0x5a5a5a5a and words[0x374]==280 and words[0x180]==0x40bce5ce
new_words=dict(words);new_words[0x374]=args.period;new_words[0x180]=(words[0x180]+280-args.period)&0xffffffff
assert checksum(new_words)==0x5a5a5a5a
for address in sorted([0x374,0x180],key=lambda a:locations[a][0],reverse=True):
 start,end=locations[address];body=body[:start]+f'0x{new_words[address]:08x}'+body[end:]
header.write_text(before+'static const struct fw_data f8_pro_r8_shuping_fw[] = {'+body+'};'+after)
(W/'Makefile').write_text('obj-m := f8_gsl_shuping.o\nf8_gsl_shuping-y := f8_gsl_driver.o gsl_point_id.o\nccflags-y += -I'+str(G)+'\n')
with (O/'build.log').open('w') as f:r=subprocess.run(['make','-C',str(H),'M='+str(W),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,(O/'build.log').read_text()[-3000:]
syntax=ast.parse((P/'tools/build-f8-official-touch-module.py').read_text())
exec(compile(ast.Module(body=[n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name in ['elf_sections','versions']],type_ignores=[]),'abi','exec'))
new=W/'f8_gsl_shuping.ko';assert versions(new.read_bytes())==versions(old.read_bytes())
def array(file,name,section):
 data=file.read_bytes();secs=elf_sections(data)
 line=next(l for l in subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(file)],text=True).splitlines() if l.endswith(' '+name))
 off,size=[int(v,16) for v in line.split()[:2]];sec=secs[section];return data[sec[4]+off:sec[4]+off+size]
assert array(new,'f8_pro_r8_shuping_algorithm','.data')==array(old,'f8_pro_r8_shuping_algorithm','.data')
original_fw=array(old,'f8_pro_r8_shuping_fw','.rodata');candidate_fw=array(new,'f8_pro_r8_shuping_fw','.rodata')
assert len(original_fw)==len(candidate_fw)
changes=[];page=None
for n in range(0,len(original_fw),8):
 a,v=struct.unpack_from('<II',original_fw,n);aa,vv=struct.unpack_from('<II',candidate_fw,n);assert a==aa
 if a==0xf0:page=v;assert v==vv
 elif v!=vv:changes.append({'address':hex(page*128+a),'old':hex(v),'new':hex(vv)})
assert {x['address'] for x in changes}=={'0x180','0x374'}
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(new)],check=True);shutil.copyfile(new,O/new.name)
for name in ['f8_gsl_driver.c','gsl_point_id.c','gsl_point_id.h','f8-pro-r8-shuping-reference.h']:shutil.copyfile(W/name,O/name)
report={'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'srcversion':subprocess.check_output(['modinfo','-F','srcversion',str(new)],text=True).strip(),'vermagic':subprocess.check_output(['modinfo','-F','vermagic',str(new)],text=True).strip(),'baseline_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'import_crcs_identical_to_actual_verified_baseline':True,'driver_and_algorithm_unchanged':True,'firmware_changes':changes,'firmware_checksum':'0x5a5a5a5a','period_candidate':args.period,'original_period':280,'hardware_loaded':False,'verified_hz':None,'boot_asset_modified':False,'warning':'0x374 controls acquisition timing; its effect on report rate must be measured before any 120Hz claim.'}
(O/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
