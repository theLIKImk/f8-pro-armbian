"""Fetch Weston 15.0.1 source against the exact Arch recipe hash and release keys."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('fetch', ROOT/'tools/fetch-plasma-sources.py')
fetcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)
recipe=ROOT/'downloads/weston15-packaging'
text=(recipe/'PKGBUILD').read_text()
expected=re.search(r"sha256sums=\('([0-9a-f]{64})'",text)[1]
assert expected=='551d039bfb0c837ba5a4d027cdb8ee16bded0eedb789821f8025d8a64b791f6d'
allowed=set(re.findall(r"'([0-9A-F]{40})'",text))
cache=ROOT/'downloads/weston-15.0.1';cache.mkdir(parents=True,exist_ok=True)
archive=cache/'weston-15.0.1.tar.xz'
urls=['https://gitlab.freedesktop.org/wayland/weston/-/releases/15.0.1/downloads/weston-15.0.1.tar.xz',
      'https://wayland.freedesktop.org/releases/weston-15.0.1.tar.xz']
used=None
for url in urls:
    try:
        print('Fetching '+url,flush=True)
        data=archive.read_bytes() if archive.exists() else fetcher.fetch(url,32*1024**2)
        assert hashlib.sha256(data).hexdigest()==expected
        signature=fetcher.fetch(url+'.sig',65536)
        archive.write_bytes(data);(cache/'weston-15.0.1.tar.xz.sig').write_bytes(signature)
        used=url;break
    except Exception as error:
        print(type(error).__name__+': '+str(error)[:200],flush=True)
if not used:raise RuntimeError('No verified official source download')
home=Path('/var/tmp/f8-pro-archlinux-20261027/weston-verification-20261028')
home.mkdir(mode=0o700,exist_ok=True);home.chmod(0o700)
gpg=['gpg','--batch','--homedir',str(home)]
subprocess.run(gpg+['--import',*[str(f) for f in (recipe/'keys/pgp').glob('*.asc')]],check=True,capture_output=True)
r=subprocess.run(gpg+['--status-fd=1','--verify',str(archive)+'.sig',str(archive)],check=True,capture_output=True,text=True)
valid=[line.split()[2:] for line in r.stdout.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
assert any(f[0] in allowed or f[-1] in allowed for f in valid)
report=ROOT/'analysis/weston-15.0.1';report.mkdir(parents=True,exist_ok=True)
(report/'source.json').write_text(json.dumps({'source_url':used,'sha256':expected,'signature_verified':True,
    'validsig_fields':valid,'recipe_tag':'15.0.1-3','recipe_commit':'62bf7fd53abcc1d3eb2f9c1cf941dc2daf5a50c5'},indent=2)+'\n')
(report/'gpg-status.txt').write_text(r.stdout)
print('Weston SHA256 and release signature PASS',flush=True)
