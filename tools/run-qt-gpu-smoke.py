"""Upload, compile and run a bounded Qt EGLFS test over the existing SSH link."""
from pathlib import Path
import subprocess
import sys
import json
import re

PROJECT = Path(__file__).resolve().parent.parent
BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
HOST = 'alarm@192.168.1.227'
OPTIONS = ['-i', str(BASE/'private-keys/f8-pro-test-ed25519'), '-o', 'BatchMode=yes',
           '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'UserKnownHostsFile='+str(BASE/'test-known-hosts'), '-o', 'ConnectTimeout=8',
           '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2']


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run inside the existing build WSL')
    remote = subprocess.run(['ssh', '-T', *OPTIONS, HOST,
                             'mktemp -d /tmp/f8-qt-gpu-XXXXXXXX'],
                            check=True, capture_output=True, text=True, timeout=25).stdout.strip()
    if not re.fullmatch(r'/tmp/f8-qt-gpu-[A-Za-z0-9]{8}', remote):
        raise ValueError('Unexpected remote directory')
    sources = PROJECT/'tools/qt-gpu-smoke'
    subprocess.run(['scp', *OPTIONS, *[str(sources/name) for name in
                   ('main.cpp', 'main.qml', 'plasma.qml', 'CMakeLists.txt')], HOST+':'+remote+'/'],
                   check=True, timeout=60)
    script = 'cd '+remote+'\n'+r'''
set -eu
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
mkdir -m 700 runtime
set +e
timeout --signal=TERM --kill-after=5 25 env \
 LD_LIBRARY_PATH=/opt/f8-pro/vendor-gpu-g13p0-20261028/lib \
 XDG_RUNTIME_DIR="$PWD/runtime" \
 QT_QPA_PLATFORM=eglfs QT_QPA_EGLFS_INTEGRATION=eglfs_kms \
 QT_QPA_EGLFS_ALWAYS_SET_MODE=1 QT_QPA_EGLFS_KMS_ATOMIC=0 \
 QSG_RHI_BACKEND=opengl QT_LOGGING_RULES='qt.qpa.*=true;qt.scenegraph.general=true' \
 ./build/f8-qt-gpu-smoke >test.log 2>&1
result=$?
cat test.log
printf '\nF8_QT_EXIT=%s\n' "$result"
exit "$result"
'''
    result = subprocess.run(['ssh', '-T', *OPTIONS, HOST, 'sh -s'],
                            input=script, capture_output=True, text=True, timeout=180)
    report = PROJECT/'analysis/arch-gpu'
    report.mkdir(parents=True, exist_ok=True)
    log = result.stdout+result.stderr
    (report/'qt-eglfs-smoke.log').write_text(log)
    passed = result.returncode == 0 and 'F8_RESULT hardware=1 frame=1' in log
    captured = 'F8_CAPTURE saved=1 width=1200 height=1920' in log
    if captured:
        subprocess.run(['scp', *OPTIONS, HOST+':'+remote+'/build/test-frame.png',
                        str(report/'qt-eglfs-frame.png')], check=True, timeout=30)
    (report/'qt-eglfs-smoke.json').write_text(json.dumps({
        'remote_work_directory': remote, 'exit_code': result.returncode,
        'hardware_renderer_and_frame_passed': passed,
        'physical_screen_confirmed': False,
        'framebuffer_capture_saved': captured,
        'latin_and_chinese_glyphs_available': 'F8_FONT latin=1 chinese=1' in log,
        'native_x11_desktop_tested': False, 'wayland_desktop_tested': False
    }, indent=2)+'\n')
    print('\n'.join(line for line in log.splitlines()
                    if 'F8_' in line or 'QT[1]' in line or 'QT[2]' in line or 'QT[3]' in line))
    return 0 if passed else (result.returncode or 3)


if __name__ == '__main__':
    raise SystemExit(main())
