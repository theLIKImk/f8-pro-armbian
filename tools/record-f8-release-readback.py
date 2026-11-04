"""Record completed native reads, normalizing console-encoded Windows paths."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-armbian-r1'
m=json.loads((O/'image-manifest.json').read_text());results=[]
for kind in ['boot','rootfs']:
 p=O/'flash-files'/(kind+'-check.json')
 try:text=p.read_text(encoding='utf-8')
 except UnicodeDecodeError:text=p.read_text(encoding='gb18030')
 data=json.loads(text)
 prefix='boot' if kind=='boot' else 'root'
 image=(O/'flash-files'/m[prefix+'_file']).resolve()
 assert data['result']=='PASS' and data['sha256']==m[prefix+'_sha256'] and data['bytes']==image.stat().st_size
 data['image']=str(image);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');results.append(data)
bundle=json.loads((O/'bundle.json').read_text());assert bundle['all_zip_entries_verified']
bundle['raw_flash_files_full_readback_verified']=True
(O/'bundle.json').write_text(json.dumps(bundle,indent=2)+'\n')
(O/'flash-files/native-readback.json').write_text(json.dumps({'all_passed':True,'checks':results,'target_partition_written':False},indent=2)+'\n')
print('Completed bundle and full native image readback recorded')
