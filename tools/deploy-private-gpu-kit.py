"""Verify and copy the factory GPU test kit to an isolated target /opt prefix.

No ldconfig, service configuration, global library links or environment changes.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent.parent
BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
HOST = 'alarm@192.168.1.227'
OPTIONS = ['-i', str(BASE/'private-keys/f8-pro-test-ed25519'), '-o', 'BatchMode=yes',
           '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'UserKnownHostsFile='+str(BASE/'test-known-hosts'), '-o', 'ConnectTimeout=8']


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run in the existing WSL')
    record = json.loads((PROJECT/'analysis/vendor-userspace/private-gpu-kit.json').read_text())
    archive = PROJECT/'outputs'/record['file']
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != record['sha256'] or record['target_prefix'] != '/opt/f8-pro/vendor-gpu-g13p0-20261028':
        raise ValueError('Unexpected archive or target prefix')
    remote = subprocess.run(['ssh', '-T', *OPTIONS, HOST, 'mktemp -d /tmp/f8-gpu-kit-XXXXXXXX'], capture_output=True, text=True, check=True).stdout.strip()
    if not re.fullmatch(r'/tmp/f8-gpu-kit-[A-Za-z0-9]{8}', remote):
        raise ValueError('Unexpected upload directory')
    remote_archive = remote+'/kit.tar.gz'
    subprocess.run(['scp', *OPTIONS, str(archive), HOST+':'+remote_archive], check=True, timeout=180)
    header = f'ARCHIVE={remote_archive!r}\nTARGET={record["target_prefix"]!r}\nSHA256={digest!r}\n'
    body = r'''
from pathlib import Path, PurePosixPath
import hashlib,json,subprocess,tarfile
source=Path(ARCHIVE); target=Path(TARGET)
with source.open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==SHA256
if target.exists(): raise RuntimeError('Private prefix exists; refusing overwrite')
with tarfile.open(source,'r:gz') as archive:
    members=archive.getmembers()
    for member in members:
        path=PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts: raise RuntimeError('Unsafe kit path')
        if not (member.isfile() or member.issym()): raise RuntimeError('Unexpected kit entry')
        if member.issym() and (PurePosixPath(member.linkname).is_absolute() or '..' in PurePosixPath(member.linkname).parts):
            raise RuntimeError('Unsafe kit link')
    target.mkdir(parents=True,mode=0o755)
    archive.extractall(target,filter='data')
manifest=json.loads((target/'source-manifest.json').read_text())
for entry in manifest['files']:
    path=target/('copyright' if entry['file']=='copyright' else 'lib/'+entry['file'])
    with path.open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==entry['sha256']
for name in ('libmali.so.1.9.0','libEGL.so.1','libGLESv2.so.2','libgbm.so.1'):
    result=subprocess.run(['/usr/lib/ld-linux-aarch64.so.1','--library-path',str(target/'lib'),'--list',str(target/'lib'/name)],capture_output=True,text=True)
    (target/(name+'.loader.txt')).write_text(result.stdout+result.stderr)
    if result.returncode: raise RuntimeError('Native private GPU dependency resolution failed: '+name)
print('Private GPU kit installed and hashes/native dependencies verified: '+str(target))
'''
    subprocess.run(['ssh', '-T', *OPTIONS, HOST, 'sudo -n python3 -'], input=(header+body).encode(), check=True, timeout=180)
    record['installed_on_arch'] = True
    record['native_loader_resolution_passed'] = True
    (PROJECT/'analysis/vendor-userspace/private-gpu-kit.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    main()
