"""Build only Weston's GL module with its upstream older-GBM allocation branch."""
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',ROOT/'tools/build-plasma-activities.py')
connection=importlib.util.module_from_spec(spec);spec.loader.exec_module(connection)


def main():
    if sys.platform!='linux':raise SystemExit('Run inside build WSL')
    source=ROOT/'downloads/weston-15.0.1/weston-15.0.1.tar.xz'
    metadata=json.loads((ROOT/'analysis/weston-15.0.1/source.json').read_text())
    assert metadata['signature_verified'] and hashlib.sha256(source.read_bytes()).hexdigest()==metadata['sha256']
    remote=connection.ssh('mktemp -d /home/alarm/f8-pro-builds/weston-gl-legacy-XXXXXXXX',
                          capture_output=True,text=True,check=True,timeout=30).stdout.strip()
    assert re.fullmatch(r'/home/alarm/f8-pro-builds/weston-gl-legacy-[A-Za-z0-9]{8}',remote)
    subprocess.run(['scp',*connection.OPTIONS,str(source),connection.HOST+':'+remote+'/'],check=True,timeout=60)
    script='cd '+remote+'\nEXPECTED='+metadata['sha256']+'\n'+r'''
set -eu
export LANG=C.UTF-8 LC_ALL=C.UTF-8
printf '%s  weston-15.0.1.tar.xz\n' "$EXPECTED" | sha256sum --check
python3 - <<'PY'
import tarfile
with tarfile.open('weston-15.0.1.tar.xz') as t:
    t.extractall('source',filter='data')
PY
meson setup build source/weston-15.0.1 --buildtype=release -Db_lto=false \
 -Dbackend-drm=true -Dbackend-headless=false -Dbackend-pipewire=false \
 -Dbackend-rdp=false -Dbackend-vnc=false -Dbackend-wayland=false -Dbackend-x11=false \
 -Drenderer-gl=true -Drenderer-vulkan=false -Dxwayland=false -Dremoting=false \
 -Dpipewire=false -Dshell-desktop=false -Dshell-ivi=false -Dshell-kiosk=true \
 -Dshell-lua=false -Ddemo-clients=false -Dsimple-clients=[] -Dtools=[] \
 -Dwcap-decode=false -Dtests=false -Dtest-junit-xml=false -Ddoc=false
python3 - <<'PY'
from pathlib import Path
p=Path('build/config.h');text=p.read_text()
line='#define HAVE_GBM_BO_CREATE_WITH_MODIFIERS2 1'
assert text.count(line)==1
p.with_suffix('.original.h').write_text(text)
p.write_text(text.replace(line,'/* F8-PRO: use upstream older-GBM branch. */\n/* #undef HAVE_GBM_BO_CREATE_WITH_MODIFIERS2 */'))
PY
timeout --kill-after=15 600 ninja -C build -j2 libweston/renderer-gl/gl-renderer.so
readelf --dyn-syms --wide build/libweston/renderer-gl/gl-renderer.so >module-symbols.txt
if grep -q 'UND.*gbm_bo_create_with_modifiers2' module-symbols.txt; then exit 4; fi
sha256sum build/libweston/renderer-gl/gl-renderer.so
'''
    print('Legacy GBM module build directory: '+remote,flush=True)
    result=connection.ssh('sh -s',input=script,text=True,capture_output=True,timeout=720)
    report=ROOT/'analysis/weston-15.0.1'
    (report/'legacy-renderer-build.log').write_text(result.stdout+result.stderr)
    status={'remote_build_directory':remote,'exit_code':result.returncode,
            'upstream_older_gbm_branch_selected':True,'global_modules_modified':False}
    if result.returncode==0:
        module=remote+'/build/libweston/renderer-gl/gl-renderer.so'
        digest=re.search(r'^([0-9a-f]{64})  build/libweston/renderer-gl/gl-renderer.so$',result.stdout,re.M)[1]
        output=ROOT/'outputs/weston-15.0.1';output.mkdir(parents=True,exist_ok=True)
        subprocess.run(['scp',*connection.OPTIONS,connection.HOST+':'+module,
                        str(output/'gl-renderer-legacy-gbm.so')],check=True,timeout=60)
        assert hashlib.sha256((output/'gl-renderer-legacy-gbm.so').read_bytes()).hexdigest()==digest
        status.update(remote_module=module,module_sha256=digest)
    (report/'legacy-renderer-build.json').write_text(json.dumps(status,indent=2)+'\n')
    print(result.stdout[-6000:]+result.stderr[-2000:])
    return result.returncode


if __name__=='__main__':raise SystemExit(main())
