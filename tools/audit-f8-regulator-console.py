"""Collect pinned regulator/device-link source for interpreting R2 warnings."""
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parents[1]
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
out=P/'analysis/armbian/regulator-console-audit'
out.mkdir(parents=True,exist_ok=True)
paths=['drivers/regulator/core.c','drivers/base/core.c','drivers/tty/serial/8250/8250_dw.c',
       'drivers/video/rockchip/rga3/rga_drv.c','init/main.c']
files=[];snippets=[]
patterns=['could not add device link','device_link_add','DL_FLAG_STATELESS','rga_iommu_bind',
          'unable to open an initial console','of_alias_get_id']
for relative in paths:
    path=source/relative
    if not path.is_file():continue
    content=path.read_bytes()
    (out/relative.replace('/','--')).write_bytes(content)
    files.append({'path':relative,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
    lines=content.decode().splitlines()
    for index,line in enumerate(lines):
        if any(pattern in line for pattern in patterns):
            snippets.append({'path':relative,'line':index+1,'text':'\n'.join(lines[max(0,index-5):index+9])})
(out/'source-manifest.json').write_text(json.dumps({'scope':'Local pinned source analysis only','files':files},indent=2)+'\n')
(out/'snippets.json').write_text(json.dumps(snippets,indent=2)+'\n')
print(json.dumps([item for item in snippets if 'could not add' in item['text'] or
                 'rga_iommu_bind' in item['text'] or 'unable to open' in item['text']],indent=2))
