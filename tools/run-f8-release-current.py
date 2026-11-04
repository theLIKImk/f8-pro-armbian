from pathlib import Path
import os,subprocess,time,json,traceback
P=Path(__file__).resolve().parents[1];B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2')
start=time.monotonic()
while not (B/'snapshot-complete.json').exists():
 assert time.monotonic()-start<7200,'Snapshot wait timeout'
 time.sleep(3)
try:
 if (B/'failed.json').exists():(B/'failed.json').unlink()
 env=dict(os.environ,F8_RELEASE_DIR=str(B),DEBIAN_FRONTEND='noninteractive')
 for phase,script in [('configuring','configure-f8-release-root.py'),('privacy_audit','scrub-f8-release-current.py'),('image_build','build-f8-release-current.py')]:
  if phase=='configuring' and (B/'configured.json').exists():continue
  (B/'progress.json').write_text(json.dumps({'phase':phase,'time':time.time()})+'\n')
  with (B/(phase+'.log')).open('w') as log:r=subprocess.run(['python3',str(P/'tools'/script)],env=env,stdout=log,stderr=subprocess.STDOUT)
  assert r.returncode==0,phase+' failed; inspect '+str(B/(phase+'.log'))
except Exception as e:
 (B/'failed.json').write_text(json.dumps({'error':str(e),'time':time.time()})+'\n');raise
