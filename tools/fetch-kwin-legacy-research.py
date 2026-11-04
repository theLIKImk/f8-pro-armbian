"""Fetch signed older KWin source for read-only legacy wl_drm research."""
from pathlib import Path
import importlib.util,hashlib,json,re,subprocess,tarfile,urllib.parse
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('fetcher',root/'tools/fetch-plasma-sources.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
version='6.6.5';info='https://kde.org/info/plasma-'+version+'/'
html=f.fetch(info,2*1024**2).decode();assert f.SIGNER in html
parser=f.Rows();parser.feed(html);records=[]
for row in parser.rows:
    hashes=re.findall(r'\b[0-9a-f]{64}\b',row['text'])
    for href in row['links']:
        p=urllib.parse.urlparse(urllib.parse.urljoin(info,href))
        if p.hostname=='download.kde.org' and p.path==f'/stable/plasma/{version}/kwin-{version}.tar.xz':
            assert len(hashes)==1
            records.append((urllib.parse.urlunparse(p._replace(scheme='https')),hashes[0]))
assert len(records)==1;url,digest=records[0]
cache=root/'downloads'/('kwin-'+version);cache.mkdir(exist_ok=True)
archive=cache/('kwin-'+version+'.tar.xz')
if not archive.exists():archive.write_bytes(f.fetch(url,128*1024**2))
assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest
signature=archive.with_suffix('.xz.sig');signature.write_bytes(f.fetch(url+'.sig',65536))
gpg=['gpg','--batch','--homedir','/var/tmp/f8-pro-archlinux-20261027/plasma-verification-20261028','--status-fd=1','--verify',str(signature),str(archive)]
verified=subprocess.run(gpg,capture_output=True,text=True,check=True)
assert any(line.startswith('[GNUPG:] VALIDSIG ') and f.SIGNER in line.split() for line in verified.stdout.splitlines())
report=root/'analysis/kwin-legacy-research';report.mkdir(exist_ok=True)
(report/'source.json').write_text(json.dumps({'version':version,'official_info_url':info,'url':url,'sha256':digest,'signature_verified':True,'pinned_primary_signer':f.SIGNER,'scope':'Read-only research; not an installed older KWin package'},indent=2)+'\n')
(report/'signature-status.txt').write_text(verified.stdout)
with tarfile.open(archive) as t:
    for m in t.getmembers():
        if m.isfile() and m.name.endswith(('.cpp','.h','.xml')):
            data=t.extractfile(m).read();text=data.decode(errors='replace')
            if any(s in text for s in ['KWIN_WAYLAND_REENABLE_WL_DRM','class DrmClientBuffer','wl_drm_interface','class DrmInterface']):
                output=report/m.name.split('/',1)[1];output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
                print(m.name)
                for i,line in enumerate(text.splitlines()):
                    if any(s in line for s in ['KWIN_WAYLAND_REENABLE_WL_DRM','class DrmClientBuffer','wl_drm_interface','class DrmInterface']):print(i+1,line)
print('OFFICIAL_LEGACY_SOURCE_SHA_AND_SIGNATURE_PASS',digest)
