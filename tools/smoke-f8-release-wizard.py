from pathlib import Path
import subprocess,time,json,os,shutil
P=Path(__file__).resolve().parents[1];B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2');R=B/'rootfs';O=P/'outputs/armbian/f8-armbian-20261103-r2'
start=time.monotonic()
while not (B/'current-mkfs-complete.json').exists():
 assert time.monotonic()-start<3600
 if (B/'failed.json').exists():raise RuntimeError((B/'failed.json').read_text())
 time.sleep(3)
args=['chroot',str(R),'/usr/bin/env','QT_QPA_PLATFORM=offscreen','LANG=C.UTF-8','/usr/bin/python3','/usr/local/lib/f8-pro/first-run.py','--preview','--render-preview','/tmp/release-preview']
try:r=subprocess.run(args,capture_output=True,text=True,timeout=240)
except subprocess.TimeoutExpired as e:
 result={'exit':'timeout','stderr':(e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else (e.stderr or ''),'preview_pages':len(list((R/'tmp/release-preview').glob('page-*.png'))),'account_creation_executed':False};(O/'wizard-smoke.json').write_text(json.dumps(result,indent=2)+'\n');raise
files=sorted((R/'tmp/release-preview').glob('page-*.png'))
result={'exit':r.returncode,'preview_pages':len(files),'stderr':r.stderr[-1800:],'account_creation_executed':False,'cold_boot_test':False}
D=O/'wizard-preview';D.mkdir(exist_ok=True)
for f in files:shutil.copyfile(f,D/f.name)
(O/'wizard-smoke.json').write_text(json.dumps(result,indent=2)+'\n');assert r.returncode==0 and len(files)>=4,result
print(json.dumps(result))
