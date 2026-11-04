import json,time,statistics
from pathlib import Path
p=next(p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='f8-em30918')
samples=[]
for _ in range(14):
 samples.append({'light':int((p/'in_intensity_raw').read_text()),'proximity':int((p/'proximity_raw').read_text()),'monotonic':time.monotonic()});time.sleep(.15)
a=[s['light'] for s in samples];ps=[s['proximity'] for s in samples]
o={'condition':'user confirmed optical opening fully covered','ambient':{'min':min(a),'max':max(a),'median':statistics.median(a)},'proximity':{'min':min(ps),'max':max(ps),'median':statistics.median(ps)},'samples':samples,'register_writes':False}
b=Path('/var/lib/f8-pro/optical-baselines');b.mkdir(parents=True,exist_ok=True);(b/'dark-20261103.json').write_text(json.dumps(o,indent=2))
print(json.dumps(o))
