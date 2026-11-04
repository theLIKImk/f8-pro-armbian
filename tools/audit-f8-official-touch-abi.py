"""Read exact official touch modules/exports before porting the F8 profile."""
import hashlib
import json
from pathlib import Path
import subprocess
P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
E=P/'analysis/armbian/official-gpu-baseline-20261029'
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
headers=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
out=E/'touch-abi';out.mkdir(exist_ok=True)
symvers={}
if (headers/'Module.symvers').exists():
    for line in (headers/'Module.symvers').read_text().splitlines():
        fields=line.split()
        if len(fields)>=2:symvers[fields[1]]=int(fields[0],16)
modules=[]
for module in sorted((root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*gsl*.ko')):
    info=subprocess.check_output(['modinfo',str(module)],text=True)
    versions=subprocess.check_output(['modprobe','--show-modversions',str(module)],text=True)
    (out/(module.stem+'.modinfo.txt')).write_text(info)
    (out/(module.stem+'.versions.txt')).write_text(versions)
    mismatches=[];missing=[];count=0
    for line in versions.splitlines():
        crc,name=line.split()[:2];count+=1
        if name not in symvers:missing.append(name)
        elif int(crc,16)!=symvers[name]:mismatches.append(name)
    modules.append({'module':str(module.relative_to(root)),'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),
                    'versioned_symbols':count,'crc_mismatches_against_26_8_3_headers':mismatches,
                    'symbols_missing_from_headers':missing})
maptext=(root/'boot/System.map-6.1.115-vendor-rk35xx').read_text()
wanted=['gsl_DataInit','gsl_alg_id_main','gsl_mask_tiaoping','gsl_version_id']
exports={name:[line for line in maptext.splitlines() if line.split()[-1] in [name,'__ksymtab_'+name,'__crc_'+name]] for name in wanted}
exported={name:any('__ksymtab_'+name==line.split()[-1] for line in exports[name]) for name in wanted}
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
inventory=[str(x.relative_to(source)) for x in source.glob('gsl*')]
makefile=(source/'Makefile').read_text()
gsl_rules=[s for s in makefile.splitlines() if 'gsl' in s.lower()]
definitions={}
for module in (root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*gsl*.ko'):
    names=subprocess.check_output(['aarch64-linux-gnu-nm','--defined-only',str(module)],text=True)
    definitions[module.name]=[s for s in names.splitlines() if any(s.endswith(' '+name) for name in wanted)]
def config(text):
    return {s.split('=',1)[0]:s.split('=',1)[1] for s in text.splitlines() if s.startswith('CONFIG_') and '=' in s}
actual=config((root/'boot/config-6.1.115-vendor-rk35xx').read_text())
prior=config((headers/'.config').read_text())
differences=[{'key':k,'official_image':actual.get(k),'headers_26_8_3':prior.get(k)}
             for k in sorted(set(actual)|set(prior)) if actual.get(k)!=prior.get(k)]
report={'scope':'Read-only ABI and touch inventory, no module compilation/loading or controller writes',
        'official_image_package_version':'26.8.1','available_headers_package_version':'26.8.3',
        'stock_touch_modules':modules,'algorithm_symbols_in_kernel':exports,'algorithm_symbols_exported':exported,
        'algorithm_definitions_in_stock_modules':definitions,
        'reference_source_gsl_inventory':inventory,'reference_makefile_gsl_rules':gsl_rules,
        'kernel_config_differences':differences,
        'f8_profile_candidate_source_sha256':hashlib.sha256((P/'armbian/touch/candidate-r8-shuping/gsl3673.c').read_bytes()).hexdigest(),
        'candidate_driver_abi_validated':False,'touch_enabled':False,
        'remaining':['Verify all candidate imported CRCs against the actual official kernel',
                     'Avoid duplicate built-in GSL driver registration/algorithm ownership',
                     'Link the r8/shuping profile as a separate F8 driver before hardware enablement']}
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
