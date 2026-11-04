"""Read archived original OTG functions; no hardware access."""
import hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
symbols=json.loads((P/'analysis/armbian/touch-static/all-symbols.json').read_text())
starts=sorted({r['file_offset'] for r in symbols if r['file_offset']>=0})
image=P/'vendor/ubuntu-5.10.160/boot-assets/Image'
out=P/'analysis/armbian/vendor-otg-20261101';out.mkdir(exist_ok=True)
rows=[]
for name in ['bq25890_otg_vbus_enable','bq25890_otg_vbus_disable','bq25890_otg_vbus_is_enabled','bq25890_usb_work']:
    s=next(r for r in symbols if r['name']==name);start=s['file_offset'];end=next(v for v in starts if v>start)
    r=subprocess.run(['aarch64-linux-gnu-objdump','-D','-b','binary','-m','aarch64','--start-address='+hex(start),'--stop-address='+hex(end),str(image)],capture_output=True,text=True,check=True)
    (out/(name+'.asm')).write_text(r.stdout);rows.append({'name':name,'start':hex(start),'bytes':end-start});print(r.stdout)
(out/'manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'functions':rows},indent=2)+'\n')
