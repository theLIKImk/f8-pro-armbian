"""Exercise the downloadable merge helper with small, non-sensitive fixtures."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
source=Path(sys.argv[1]);results=[]
def h(b):return hashlib.sha256(b).hexdigest()
for case in ['valid','tampered','existing-output']:
 with tempfile.TemporaryDirectory(prefix='f8-merge-') as directory:
  d=Path(directory);shutil.copyfile(source,d/'merge-release.py');chunks=[b'first-part\x00',b'second-part\xff']
  parts=[]
  for i,b in enumerate(chunks):
   name=f'test.zip.{i+1:03d}';(d/name).write_bytes(b);parts.append({'name':name,'bytes':len(b),'sha256':h(b)})
  (d/'split-manifest.json').write_text(json.dumps({'original':{'archive':'test.zip','sha256':h(b''.join(chunks))},'parts':parts}))
  if case=='tampered':(d/parts[0]['name']).write_bytes(b'X'*len(chunks[0]))
  if case=='existing-output':(d/'test.zip').write_bytes(b'preserve')
  result=subprocess.run([sys.executable,str(d/'merge-release.py')],capture_output=True)
  if case=='valid':assert result.returncode==0 and (d/'test.zip').read_bytes()==b''.join(chunks)
  elif case=='tampered':assert result.returncode!=0 and not (d/'test.zip').exists() and not (d/'test.zip.joining').exists()
  else:assert result.returncode!=0 and (d/'test.zip').read_bytes()==b'preserve'
  results.append(case)
print(json.dumps({'passed':results}))
