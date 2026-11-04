import json
from pathlib import Path
import shutil
import argparse,re
p=argparse.ArgumentParser();p.add_argument('--round',default='t1');args=p.parse_args()
assert re.fullmatch(r't1(?:r[0-9]+)?',args.round)
P=Path(__file__).resolve().parents[1]
source=Path('F:/')
dest=P/('local/hardware/armbian-native-desktop-'+args.round+'-failure-20261030-01')
dest.mkdir(exist_ok=False)
files=[]
for p in source.iterdir():
    if p.is_file() and p.suffix.upper() in ['.TXT','.JSON','.PUB','.LOG']:
        shutil.copy2(p,dest/p.name);files.append(p.name)
(dest/'collection.json').write_text(json.dumps({'source':'F:/','files':files},indent=2)+'\n')
print('Collected '+str(len(files))+' files')
for name in ['DMSTATE.TXT','FAILED.TXT','DESKTOP.TXT','LIVELOG.TXT','TARGET.TXT','ROOTTYPE.TXT','KERNEL.TXT']:
    p=dest/name
    if p.exists():print('\n'+name+'\n'+p.read_text(errors='replace')[-13000:])
