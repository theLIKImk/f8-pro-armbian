"""Read-only comparison with the locally supplied stock Android boot kernel."""
import gzip,hashlib,json,re,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import Package,fdt,pretty
source=P.parent/'update-ANDROID12.img';pkg=Package(source)
h=pkg.read('boot',0,4096);assert h[:8]==b'ANDROID!'
size=struct.unpack_from('<I',h,8)[0];page=struct.unpack_from('<I',h,36)[0]
assert page in [2048,4096,8192] and size<128*1024*1024
kernel=pkg.read('boot',page,size)
compression='none'
if kernel[:2]==b'\x1f\x8b':kernel=gzip.decompress(kernel);compression='gzip'
assert kernel[56:60]==b'ARM\x64','Inspect compression before assuming an ARM64 Image'
O=P/'analysis/armbian/android-touch-20261102';O.mkdir(exist_ok=True)
image=O/'Image';assert not image.exists() or image.read_bytes()==kernel;image.write_bytes(kernel)
report={'source':str(source),'source_bytes':source.stat().st_size,'boot_entry':pkg.entries['boot'],'kernel_bytes':len(kernel),'kernel_sha256':hashlib.sha256(kernel).hexdigest(),'compression':compression,'linux_versions':[m.decode(errors='replace') for m in re.findall(rb'Linux version [^\x00\r\n]{1,300}',kernel)],'reference_arrays':{}}
for name in ['firmware-reference.bin','algorithm-reference.bin']:
 blob=(P/'armbian/touch/reference-r8-shuping'/name).read_bytes();i=kernel.find(blob)
 report['reference_arrays'][name]={'reference_sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'exact_full_match_in_android_kernel':i>=0,'offset':i if i>=0 else None}
report['dtb_touch_nodes']={}
for path in sorted((P/'analysis/update-ANDROID12').glob('dtb-*.dtb')):
 nodes=fdt(path.read_bytes());report['dtb_touch_nodes'][path.name]={n:{k:pretty(v) for k,v in p.items()} for n,p in nodes.items() if b'gsl' in p.get('compatible',b'').lower()}
(O/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
