"""Download the catalog-selected official KDE baseline, never flash any device."""
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request

P=Path(__file__).resolve().parents[1]
name='Armbian_26.8.1_Orangepi5_resolute_vendor_6.1.115_kde-plasma_desktop.img.xz'
catalog=json.loads((P/'analysis/armbian/official-gpu-baseline-20261029/image-catalogs/catalog.json').read_text())
assert name in next(x for x in catalog if x['name']=='archive')['selected']
out=P/'downloads/armbian/official-desktop-26.8.1';out.mkdir(parents=True,exist_ok=True)
evidence=P/'analysis/armbian/official-gpu-baseline-20261029'
base='https://dl.armbian.com/orangepi5/archive/'
def request(url,headers=None):
    return urllib.request.urlopen(urllib.request.Request(url,headers={
        'User-Agent':'F8-PRO-official-Armbian-baseline',**(headers or {})}),timeout=60)
for suffix in ['.sha','.asc']:
    dest=out/(name+suffix)
    if not dest.exists():
        with request(base+name+suffix) as response:
            dest.write_bytes(response.read())
expected=re.search(r'\b[0-9a-fA-F]{64}\b',(out/(name+'.sha')).read_text()).group().lower()
dest=out/name
part=out/(name+'.part')
if not dest.exists():
    start=part.stat().st_size if part.exists() else 0
    with request(base+name,{'Range':f'bytes={start}-'} if start else {}) as response:
        if start and response.status!=206:
            raise RuntimeError('Server did not accept resume; preserved partial file')
        if start:
            assert response.headers.get('Content-Range','').startswith(f'bytes {start}-')
        total=start+int(response.headers['Content-Length']) if response.headers.get('Content-Length') else None
        print(json.dumps({'status':'downloading','total_bytes':total,'resume_bytes':start,'final_url':response.url}),flush=True)
        last=time.monotonic();count=start
        with part.open('ab' if start else 'xb') as stream:
            while chunk:=response.read(1024*1024):
                stream.write(chunk);count+=len(chunk)
                if time.monotonic()-last>=15:
                    print(json.dumps({'downloaded_bytes':count,'total_bytes':total}),flush=True)
                    last=time.monotonic()
        if total is not None:assert part.stat().st_size==total
    with part.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    assert actual==expected, 'Downloaded image checksum mismatch; partial file retained'
    part.rename(dest)
with dest.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
assert actual==expected
report={'date':'2026-10-29','role':'Official Armbian KDE image as porting source; not F8-PRO flash image',
        'name':name,'source_url':base+name,'project_relative_path':dest.relative_to(P).as_posix(),
        'bytes':dest.stat().st_size,'sha256':actual,'published_checksum_matches':True,
        'signature_downloaded':True,'signature_verified':False,
        'image_extracted':False,'hardware_test_performed':False,'deployment_performed':False}
(evidence/'downloaded-desktop.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
