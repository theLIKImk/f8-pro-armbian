"""Build the reviewed Plasma Activities recipe on the ARM64 tablet, without installing it."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import argparse
import tarfile

PROJECT = Path(__file__).resolve().parent.parent
BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
HOST = 'alarm@192.168.1.227'
OPTIONS = ['-i', str(BASE/'private-keys/f8-pro-test-ed25519'),
           '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
           '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
           '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=3',
           '-o', 'UserKnownHostsFile='+str(BASE/'test-known-hosts')]
SIGNER = '0AAC775BB6437A8D9AF7A3ACFE0784117FBCE11D'


def ssh(command, **kwargs):
    return subprocess.run(['ssh', '-T', *OPTIONS, HOST, command], **kwargs)


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run inside the existing build WSL')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', default='plasma-activities', choices=[
        'plasma-activities', 'layer-shell-qt', 'kwayland', 'knighttime', 'kdecoration', 'libplasma',
        'kglobalacceld', 'aurorae', 'breeze', 'libkscreen', 'milou', 'kscreenlocker', 'kpipewire', 'kwin',
        'qqc2-breeze-style', 'plasma-integration', 'plasma-keyboard',
        'plasma-activities-stats', 'kactivitymanagerd', 'kde-cli-tools',
        'libksysguard', 'ksystemstats', 'plasma5support', 'plasma-workspace',
        'xdg-desktop-portal-kde', 'systemsettings', 'kmenuedit', 'polkit-kde-agent',
        'kscreen', 'plasma-desktop', 'powerdevil', 'ocean-sound-theme'])
    parser.add_argument('--resume-directory')
    parser.add_argument('--build-timeout',type=int,default=600)
    parser.add_argument('--jobs',type=int,choices=range(1,5),default=2)
    args=parser.parse_args()
    if not 60<=args.build_timeout<=3000:parser.error('build timeout must be 60..3000 seconds')
    name = args.package
    source_name={'polkit-kde-agent':'polkit-kde-agent-1'}.get(name,name)
    filename = source_name+'-6.7.5.tar.xz'
    cache = PROJECT/'downloads/plasma-6.7.5'
    manifest = json.loads((PROJECT/'analysis/plasma-6.7.5/sources.json').read_text())
    family=set(manifest['packages'])
    graph=json.loads((PROJECT/'analysis/plasma-6.7.5/recipe-dependencies.json').read_text())
    for component in graph['recipes'].values():
        family.update(component['package_names'])
    installed=ssh('pacman -Q',check=True,capture_output=True,text=True,timeout=30).stdout
    for line in installed.splitlines():
        package,version=line.split()
        if package in family and not version.startswith('6.7.5-'):
            raise RuntimeError('Refusing build with inconsistent Plasma dependency: '+line)
    record = manifest['packages'][source_name]
    # The source inventory may be undergoing an incremental refresh. Perform
    # our own SHA and pinned-signature check, rather than relying on its flags.
    assert manifest['pinned_primary_signer'] == SIGNER
    assert hashlib.sha256((cache/filename).read_bytes()).hexdigest() == record['sha256']
    verified = subprocess.run(['gpg', '--batch', '--homedir',
        str(BASE/'plasma-verification-20261028'), '--status-fd=1', '--verify',
        str(cache/(filename+'.sig')), str(cache/filename)], capture_output=True, text=True, check=True)
    assert any(line.startswith('[GNUPG:] VALIDSIG ') and SIGNER in line.split()
               for line in verified.stdout.splitlines())
    recipe = PROJECT/'packaging/plasma-6.7.5'/name
    origin = json.loads((recipe/'origin.json').read_text())
    package_arch=origin.get('package_architecture','aarch64')
    data_only=origin.get('data_only',False)
    assert package_arch in ('any','aarch64') and (package_arch!='any' or data_only)
    assert hashlib.sha256((recipe/'PKGBUILD').read_bytes()).hexdigest() == origin['recipe_sha256']
    auxiliary=[]
    for auxiliary_name, digest in origin.get('auxiliary_sources',{}).items():
        assert re.fullmatch(r'[A-Za-z0-9_.-]+',auxiliary_name) and '..' not in auxiliary_name
        path=recipe/auxiliary_name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        auxiliary.append(str(path))
    package_release = re.search(r'^pkgrel=(\d+\.\d+)$', (recipe/'PKGBUILD').read_text(), re.M)[1]
    package_prefix = name+'-6.7.5-'+package_release+'-'+package_arch
    if args.resume_directory:
        remote=args.resume_directory
    else:
        remote = ssh('mkdir -p /home/alarm/f8-pro-builds && '
                 'mktemp -d /home/alarm/f8-pro-builds/'+name+'-6.7.5-XXXXXXXX',
                 check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if not re.fullmatch(r'/home/alarm/f8-pro-builds/'+re.escape(name)+r'-6\.7\.5-[A-Za-z0-9]{8}', remote):
        raise ValueError('Unexpected build directory')
    if args.resume_directory:
        active=ssh('pgrep -x makepkg',capture_output=True,text=True,timeout=20)
        if active.returncode==0:raise RuntimeError('Wait for other makepkg processes before resuming')
        actual=ssh('sha256sum '+remote+'/PKGBUILD',check=True,capture_output=True,text=True,timeout=20).stdout.split()[0]
        assert actual==origin['recipe_sha256'],'Remote recipe differs; review before resuming'
    else:
        subprocess.run(['scp', *OPTIONS, str(recipe/'PKGBUILD'), str(cache/filename),
                    str(cache/(filename+'.sig')), str(cache/'plasma-signing-keys.pgp'), *auxiliary,
                    HOST+':'+remote+'/'], check=True, timeout=120)
    subprocess.run(['scp', *OPTIONS, str(PROJECT/'tools/native-build-supervisor.py'),
                    HOST+':'+remote+'/native-build-supervisor.py'], check=True, timeout=30)
    script = 'cd '+remote+'\nF8_PACKAGE_PREFIX='+package_prefix+'\nF8_BUILD_TIMEOUT='+str(args.build_timeout)+'\nF8_JOBS='+str(args.jobs)+'\nF8_RESUME='+str(int(bool(args.resume_directory)))+'\n'+r'''
set -eu
[ "$(id -u)" != 0 ]
[ "$(uname -m)" = aarch64 ]
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export GNUPGHOME="$PWD/gnupg"
mkdir .f8-build-active
trap 'gpgconf --kill gpg-agent >/dev/null 2>&1 || true; rmdir .f8-build-active 2>/dev/null || true' EXIT
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"
gpg --batch --import plasma-signing-keys.pgp >key-import.log 2>&1
pacman -Q >installed-packages.txt
export CMAKE_BUILD_PARALLEL_LEVEL="$F8_JOBS" MAKEFLAGS="-j$F8_JOBS"
set +e
set -- --timeout "$F8_BUILD_TIMEOUT"
if [ "$F8_RESUME" = 1 ]; then
    set -- "$@" --resume
    if [ -f build.log ]; then cp build.log build-before-resume.log; fi
fi
python3 native-build-supervisor.py "$@" >build.log 2>&1
result=$?
set -e
tail -n 45 build.log
printf '\nF8_BUILD_EXIT=%s\n' "$result"
[ "$result" = 0 ] || exit "$result"
makepkg --printsrcinfo >built.SRCINFO
for package in "$F8_PACKAGE_PREFIX".pkg.tar.*; do
    [ -f "$package" ] || exit 4
    case "$package" in *.sig) continue;; esac
    sha256sum "$package"
    bsdtar -xOf "$package" .PKGINFO
done
'''
    print('Native ARM64 build directory: '+remote, flush=True)
    result = ssh('sh -s', input=script, capture_output=True, text=True, timeout=args.build_timeout+120)
    reports = PROJECT/'analysis/plasma-6.7.5'
    (reports/(name+'-native-build-console.log')).write_text(result.stdout+result.stderr)
    subprocess.run(['scp', *OPTIONS, HOST+':'+remote+'/build.log',
                    str(reports/(name+'-native-build.log'))], check=True, timeout=60)
    thermal_log=reports/(name+'-thermal-history.csv')
    if ssh('test -f '+remote+'/thermal-history.csv',timeout=20).returncode==0:
        subprocess.run(['scp',*OPTIONS,HOST+':'+remote+'/thermal-history.csv',
                        str(thermal_log)],check=True,timeout=30)
    status = {'remote_build_directory': remote, 'exit_code': result.returncode,
              'arm64_package_built': False, 'package_installed': False,
              'jobs':args.jobs,'thermal_start_limit_milli_celsius':70000,
              'thermal_stop_limit_milli_celsius':82000,
              'thermal_stop_or_defer':any(marker in (result.stdout+result.stderr) for marker in
                                         ('F8_THERMAL_STOP','F8_THERMAL_DEFER')),
              'source_sha256': record['sha256'], 'source_primary_signer': SIGNER}
    if result.returncode == 0:
        digest = re.search(r'^([0-9a-f]{64})  ('+re.escape(package_prefix)+r'\.pkg\.tar\.(?:xz|zst))$', result.stdout, re.M)
        if not digest or 'arch = '+package_arch not in result.stdout:
            raise ValueError('Missing package hash or expected architecture metadata')
        package = digest[2]
        output = PROJECT/'outputs/plasma-6.7.5'
        output.mkdir(parents=True, exist_ok=True)
        subprocess.run(['scp', *OPTIONS, HOST+':'+remote+'/'+package, str(output/package)],
                       check=True, timeout=120)
        assert hashlib.sha256((output/package).read_bytes()).hexdigest() == digest[1]
        elves = []
        with tarfile.open(output/package) as archive:
            info = archive.extractfile('.PKGINFO').read().decode()
            buildinfo = archive.extractfile('.BUILDINFO').read().decode()
            assert '\narch = '+package_arch+'\n' in info and '\npkgname = '+name+'\n' in info
            for member in archive.getmembers():
                if member.isfile():
                    header = archive.extractfile(member).read(20)
                    if header[:4] == b'\x7fELF':
                        assert header[4:6] == bytes([2, 1]) and int.from_bytes(header[18:20], 'little') == 183
                        elves.append(member.name)
        assert not elves if data_only else elves
        (reports/(name+'-PKGINFO.txt')).write_text(info)
        (reports/(name+'-BUILDINFO.txt')).write_text(buildinfo)
        status.update(arm64_package_built=True, package=package, package_sha256=digest[1],
                      size_bytes=(output/package).stat().st_size, elf_architecture_checked=elves,
                      package_architecture=package_arch,data_only=data_only)
        extras=[]
        for data_name in origin.get('data_packages',[]):
            assert data_name in graph['recipes'][name]['package_names']
            extra_file=data_name+'-6.7.5-'+package_release+'-aarch64.pkg.tar.xz'
            extra_remote=remote+'/'+extra_file
            extra_sha=ssh('sha256sum '+extra_remote,check=True,capture_output=True,text=True,timeout=30).stdout.split()[0]
            subprocess.run(['scp',*OPTIONS,HOST+':'+extra_remote,str(output/extra_file)],check=True,timeout=90)
            assert hashlib.sha256((output/extra_file).read_bytes()).hexdigest()==extra_sha
            with tarfile.open(output/extra_file) as archive:
                info=archive.extractfile('.PKGINFO').read().decode()
                assert '\npkgname = '+data_name+'\n' in info and '\npkgver = 6.7.5-'+package_release+'\n' in info
                for member in archive.getmembers():
                    if member.isfile():assert archive.extractfile(member).read(4)!=b'\x7fELF','Expected data-only split package'
            (reports/(data_name+'-PKGINFO.txt')).write_text(info)
            extras.append({'package_name':data_name,'package':extra_file,'package_sha256':extra_sha,
                           'size_bytes':(output/extra_file).stat().st_size,'data_only':True,'package_installed':False})
        status['additional_artifacts']=extras
        origin['additional_package_sha256']={a['package_name']:a['package_sha256'] for a in extras}
        origin.update(built=True, package_sha256=digest[1])
        (recipe/'origin.json').write_text(json.dumps(origin, indent=2)+'\n')
    (reports/(name+'-native-build.json')).write_text(json.dumps(status, indent=2)+'\n')
    print(result.stdout[-10000:]+result.stderr[-2000:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
