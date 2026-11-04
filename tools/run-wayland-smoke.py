"""Bounded Weston or KWin DRM/GLES and Qt test in a transient PAM/VT session."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import argparse

PROJECT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('native_build', PROJECT/'tools/build-plasma-activities.py')
connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connection)


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run inside build WSL')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-renderer',action='store_true')
    parser.add_argument('--egl-bridge',action='store_true')
    parser.add_argument('--duration',type=int,default=8,choices=range(1,36))
    parser.add_argument('--default-gl-format',action='store_true')
    parser.add_argument('--plasma-controls',action='store_true')
    parser.add_argument('--private-platform-theme',action='store_true')
    parser.add_argument('--compositor',choices=['weston','kwin'],default='weston')
    parser.add_argument('--virtual-keyboard',action='store_true')
    parser.add_argument('--wayland-debug',action='store_true')
    parser.add_argument('--mali-protocol-trace',action='store_true')
    parser.add_argument('--mali-buffer-sharing',action='store_true')
    args=parser.parse_args()
    if args.mali_buffer_sharing and args.compositor!='kwin':
        parser.error('Mali RGB adapter test is a KWin-only option')
    if args.virtual_keyboard and (args.compositor!='kwin' or not args.egl_bridge or not args.private_platform_theme):
        parser.error('Virtual keyboard test requires KWin, EGL bridge and the private platform theme')
    qt = json.loads((PROJECT/'analysis/arch-gpu/qt-eglfs-smoke.json').read_text())
    source = qt['remote_work_directory']
    if not qt['hardware_renderer_and_frame_passed'] or not re.fullmatch(r'/tmp/f8-qt-gpu-[A-Za-z0-9]{8}', source):
        raise ValueError('Expected previously tested native Qt client')
    remote = connection.ssh('mktemp -d /tmp/f8-wayland-XXXXXXXX', check=True,
                            capture_output=True, text=True, timeout=30).stdout.strip()
    if not re.fullmatch(r'/tmp/f8-wayland-[A-Za-z0-9]{8}', remote):
        raise ValueError('Unexpected work directory')
    user_script = f'cd {remote}\ncp {source}/build/f8-qt-gpu-smoke {source}/build/main.qml .\n'+r'''
set -eu
ulimit -c 0
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export XDG_RUNTIME_DIR=/run/user/1000
export LIBSEAT_BACKEND=logind
export LD_LIBRARY_PATH=/opt/f8-pro/vendor-gpu-g13p0-20261028/lib
loginctl show-session "$XDG_SESSION_ID" >session.txt
weston --backend=drm --renderer=gl --drm-device=card0 --seat=seat0 \
 --shell=kiosk-shell.so --no-config --socket=wayland-f8-test --idle-time=0 \
 --log="$PWD/weston.log" >weston-stdio.log 2>&1 &
compositor=$!
trap 'kill "$compositor" 2>/dev/null || true; wait "$compositor" 2>/dev/null || true' EXIT HUP INT TERM
count=0
while [ ! -S "$XDG_RUNTIME_DIR/wayland-f8-test" ]; do
    kill -0 "$compositor" 2>/dev/null || { cat weston.log; exit 4; }
    count=$((count+1))
    [ "$count" -lt 40 ] || exit 5
    sleep 0.25
done
export WAYLAND_DISPLAY=wayland-f8-test QT_QPA_PLATFORM=wayland
export QT_WAYLAND_CLIENT_BUFFER_INTEGRATION=wayland-egl QSG_RHI_BACKEND=opengl
export QT_DEBUG_PLUGINS=1
set +e
timeout --kill-after=3 40 ./f8-qt-gpu-smoke >client.log 2>&1
client_result=$?
set -e
cat client.log
exit "$client_result"
'''
    user_script=user_script.replace('export QT_DEBUG_PLUGINS=1',
        'export QT_DEBUG_PLUGINS=1\nexport F8_TEST_DURATION_MS='+str(args.duration*1000),1)
    if args.wayland_debug:
        user_script=user_script.replace('export QT_DEBUG_PLUGINS=1',
            'export QT_DEBUG_PLUGINS=1\nexport WAYLAND_DEBUG=client',1)
    if args.compositor=='kwin':
        if args.legacy_renderer:parser.error('Legacy GL module is a Weston-only option')
        kwin=json.loads((PROJECT/'analysis/plasma-6.7.5/kwin-native-build.json').read_text())
        assert kwin['arm64_package_built'] and kwin['package_installed']
        start=user_script.index('weston --backend=drm')
        end=user_script.index('compositor=$!',start)
        user_script=user_script[:start]+'''export KWIN_COMPOSE=O2ES
export KWIN_DRM_DEVICES=/dev/dri/card0
export XCURSOR_THEME=breeze_cursors XCURSOR_SIZE=32
export QT_LOGGING_RULES='kwin*.debug=true;kwin_core.info=true'
kwin_wayland --drm --socket=wayland-f8-test --no-lockscreen --no-global-shortcuts --no-kactivities >weston.log 2>&1 &
'''+user_script[end:]
        user_script=user_script.replace('cat client.log',
            'timeout 5 /usr/lib/qt6/bin/qdbus org.kde.KWin /KWin org.kde.KWin.supportInformation >compositor-support.txt 2>support-error.log || true\ncat client.log',1)
        if args.mali_buffer_sharing:
            user_script=user_script.replace('export KWIN_COMPOSE=O2ES',
                'export F8_PRO_MALI_BUFFER_SHARING=1\nexport KWIN_COMPOSE=O2ES',1)
    if args.plasma_controls:
        user_script=user_script.replace('set -eu','cp '+source+'/build/plasma.qml .\nset -eu',1)
        user_script=user_script.replace('export QT_DEBUG_PLUGINS=1','export QT_DEBUG_PLUGINS=1\nexport F8_TEST_UI=plasma',1)
    if args.default_gl_format:
        user_script=user_script.replace('export QT_DEBUG_PLUGINS=1','export QT_DEBUG_PLUGINS=1\nexport F8_USE_DEFAULT_GL_FORMAT=1',1)
    theme_prefix=None
    if args.private_platform_theme:
        theme=json.loads((PROJECT/'analysis/plasma-6.7.5/plasma-integration-native-build.json').read_text())
        assert theme['arm64_package_built']
        theme_directory=theme['remote_build_directory']
        assert re.fullmatch(r'/home/alarm/f8-pro-builds/plasma-integration-6\.7\.5-[A-Za-z0-9]{8}',theme_directory)
        theme_prefix=theme_directory+'/pkg/plasma-integration/usr/lib/qt6/plugins'
        user_script=user_script.replace('export QT_DEBUG_PLUGINS=1',
            'export QT_DEBUG_PLUGINS=1\nexport F8_PRO_WAYLAND_GLES=1\nexport QT_QPA_PLATFORMTHEME=kde\nexport QT_PLUGIN_PATH='+theme_prefix,1)
    module=None
    if args.mali_protocol_trace:
        if args.compositor!='weston':parser.error('Mali protocol observer is a Weston diagnostic')
        observer=json.loads((PROJECT/'analysis/arch-gpu/mali-protocol-trace.json').read_text())['remote_module']
        assert re.fullmatch(r'/home/alarm/f8-pro-builds/mali-protocol-trace-[A-Za-z0-9]{8}/libf8-mali-protocol-trace\.so',observer)
        user_script=user_script.replace('weston --backend=drm','env LD_PRELOAD='+observer+' weston --backend=drm',1)
    if args.legacy_renderer:
        legacy=json.loads((PROJECT/'analysis/weston-15.0.1/legacy-renderer-build.json').read_text())
        assert legacy['exit_code']==0
        module=legacy['remote_module']
        assert re.fullmatch(r'/home/alarm/f8-pro-builds/weston-gl-legacy-[A-Za-z0-9]{8}/build/libweston/renderer-gl/gl-renderer\.so',module)
        user_script=user_script.replace('loginctl show-session',
            'export WESTON_MODULE_MAP=gl-renderer.so='+module+'\nloginctl show-session',1)
    bridge=None
    if args.egl_bridge:
        bridge=json.loads((PROJECT/'analysis/weston-15.0.1/egl-platform-bridge.json').read_text())['remote_module']
        assert re.fullmatch(r'/home/alarm/f8-pro-builds/egl-platform-bridge-[A-Za-z0-9]{8}/libf8-egl-platform\.so',bridge)
        user_script=user_script.replace('export QT_DEBUG_PLUGINS=1',
            'export QT_DEBUG_PLUGINS=1\nexport LD_PRELOAD='+bridge,1)
    if args.virtual_keyboard:
        keyboard=json.loads((PROJECT/'analysis/plasma-6.7.5/plasma-keyboard-native-build.json').read_text())
        assert keyboard['arm64_package_built'] and keyboard['package_installed']
        # KWin passes its privileged WAYLAND_SOCKET to the input method child.
        # Keep the compatibility environment in that child, not KWin.
        wrapper='''#!/bin/sh
export LD_PRELOAD='''+bridge+'''
export QT_PLUGIN_PATH='''+theme_prefix+'''
export QT_QPA_PLATFORMTHEME=kde F8_PRO_WAYLAND_GLES=1 QSG_RHI_BACKEND=opengl
exec /usr/bin/plasma-keyboard >'''+remote+'''/keyboard.log 2>&1
'''
        user_script=user_script.replace('export KWIN_COMPOSE=O2ES',
            "cat >input-method.sh <<'F8_INPUT_METHOD_END'\n"+wrapper+
            'F8_INPUT_METHOD_END\nchmod 700 input-method.sh\nexport KWIN_COMPOSE=O2ES',1)
        user_script=user_script.replace('kwin_wayland --drm',
            'kwin_wayland --inputmethod '+remote+'/input-method.sh --drm',1)
        user_script=user_script.replace('timeout --kill-after=3 40 ./f8-qt-gpu-smoke',
            '''(
while kill -0 "$compositor" 2>/dev/null; do
    printf '\\nTIME=%s\\n' "$(date +%s)"
    timeout 2 /usr/lib/qt6/bin/qdbus org.kde.KWin /VirtualKeyboard org.freedesktop.DBus.Properties.GetAll org.kde.kwin.VirtualKeyboard || true
    sleep 1
done
) >keyboard-state.log 2>&1 &
timeout --kill-after=3 40 ./f8-qt-gpu-smoke''',1)
    connection.ssh('sh -s', input='cat >'+remote+"/run-client.sh <<'F8_SCRIPT_END'\n"+
                   user_script+'\nF8_SCRIPT_END\n', check=True, text=True, timeout=30)
    root_script = 'WORK='+repr(remote)+'\n'+r'''
import os,subprocess,json
from pathlib import Path
assert os.getuid()==0
work=Path(WORK)
unit='f8-wayland-'+work.name.split('-')[-1]
old=subprocess.run(['fgconsole'],capture_output=True,text=True)
vt=old.stdout.strip()
if old.returncode or not vt.isdecimal() or not 1<=int(vt)<=63:
    raise RuntimeError('Cannot safely determine original virtual terminal')
if subprocess.run(['systemctl','is-active','--quiet','getty@tty7.service']).returncode==0:
    raise RuntimeError('tty7 already in use by getty')
argv=['systemd-run','--unit='+unit,'--collect','--wait',
      '--property=User=alarm','--property=PAMName=login',
      '--property=TTYPath=/dev/tty7','--property=StandardInput=tty',
      '--property=TTYReset=yes','--property=TTYVHangup=yes',
      '--property=TTYVTDisallocate=yes','--property=RuntimeMaxSec=45',
      '--property=KillMode=control-group','--property=WorkingDirectory='+WORK,
      '--setenv=XDG_SESSION_TYPE=wayland','--setenv=XDG_SEAT=seat0','--setenv=XDG_VTNR=7',
      '/usr/bin/dbus-run-session','--','/bin/sh',WORK+'/run-client.sh']
try:
    subprocess.run(['chvt','7'],check=True,timeout=5)
    result=subprocess.run(argv,capture_output=True,text=True,timeout=60)
    journal=subprocess.run(['journalctl','--no-pager','-u',unit+'.service','-n','100'],capture_output=True,text=True)
    (work/'service.log').write_text(result.stdout+result.stderr+journal.stdout)
    (work/'result.json').write_text(json.dumps({'service_exit_code':result.returncode,'original_vt':int(vt)},indent=2)+'\n')
    print(result.stdout+result.stderr)
finally:
    subprocess.run(['systemctl','stop',unit+'.service'],capture_output=True,timeout=10)
    subprocess.run(['chvt',vt],check=True,timeout=5)
'''
    print('Wayland test directory: '+remote, flush=True)
    result = connection.ssh('sudo -n python3 -', input=root_script, capture_output=True,
                             text=True, timeout=90)
    output = PROJECT/'analysis/arch-gpu/wayland-smoke'
    output.mkdir(parents=True, exist_ok=True)
    (output/'launcher.log').write_text(result.stdout+result.stderr)
    evidence = output/remote.rsplit('/', 1)[-1]
    evidence.mkdir(exist_ok=False)
    subprocess.run(['scp', *connection.OPTIONS, '-r', connection.HOST+':'+remote+'/.',
                    str(evidence)], check=True, timeout=60)
    weston = (evidence/'weston.log').read_text() if (evidence/'weston.log').exists() else ''
    support=(evidence/'compositor-support.txt').read_text() if (evidence/'compositor-support.txt').exists() else ''
    client = (evidence/'client.log').read_text() if (evidence/'client.log').exists() else ''
    service=json.loads((evidence/'result.json').read_text()) if (evidence/'result.json').exists() else {}
    graphics_errors=[line for line in client.splitlines() if any(s in line for s in
        ('eglSwapBuffers failed','Could not create EGL surface','Failed to initialize graphics backend',
         'Failed to create RHI','EGL not available','Cannot find EGLConfig'))]
    record = {'remote_work_directory':remote, 'launcher_exit_code':result.returncode,
              'compositor':args.compositor,
              'kwin_compositor_test_attempted':args.compositor=='kwin',
              'full_plasma_session_tested':False,
              'physical_display_confirmed':False,
              'local_evidence_directory':str(evidence.relative_to(PROJECT)),
              'service_exit_code':service.get('service_exit_code'),
              'default_gl_format':args.default_gl_format,
              'plasma_controls_test':args.plasma_controls,
              'private_platform_theme':theme_prefix,
              'virtual_keyboard_requested':args.virtual_keyboard,
              'legacy_mali_rgb_adapter_requested':args.mali_buffer_sharing,
              'private_gl_module':module,
              'qt_client_egl_bridge':bridge,
              'compositor_software_fallback': 'QPainter compositing has been successfully initialized' in weston or 'Compositing Type: QPainter' in support,
              'compositor_mali_renderer_reported': bool(re.search(r'GL renderer.*Mali-G610',weston)) if args.compositor=='weston' else bool(re.search(r'OpenGL renderer string:\s*Mali-G610',support)),
              'compositor_gles_reported': bool(re.search(r'GL version:.*OpenGL ES',weston)) if args.compositor=='weston' else bool(re.search(r'OpenGL version string:\s*OpenGL ES',support)),
              'qt_context_and_swap_signal_seen':'F8_RESULT hardware=1 frame=1' in client,
              'qt_hardware_frame_passed':'F8_RESULT hardware=1 frame=1' in client and not graphics_errors,
              'graphics_errors':graphics_errors,
              'kde_wayland_tested':False,'touch_function_tested':False}
    record['graphics_acceptance_passed']=record['compositor_mali_renderer_reported'] and record['compositor_gles_reported'] and not record['compositor_software_fallback'] and record['qt_hardware_frame_passed'] and service.get('service_exit_code')==0 and 'blue_background=1' in client
    (output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    (evidence/'assessment.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    messages=(weston+client+result.stdout+result.stderr).splitlines()
    diagnostics=[line for line in messages if any(s in line for s in
        ('F8_','GL renderer:','Output \'DSI','QT[1]','QT[2]','QT[3]','cannot load','fatal:','status='))]
    print('\n'.join(diagnostics[-90:]))
    return 0 if record['graphics_acceptance_passed'] else 3


if __name__=='__main__':
    raise SystemExit(main())
