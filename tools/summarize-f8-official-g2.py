"""Record G2 hardware GPU, DSI and bounded Wayland evidence without overclaiming."""
import hashlib
import json
from pathlib import Path
import re
P=Path(__file__).resolve().parents[1]
logs=P/'local/hardware/armbian-official-g2-20261029-01'
def read(name):return (logs/name).read_text(encoding='utf-8')
gpu=json.loads(read('GPU.JSON'));dmesg=read('DMESG.TXT');journal=read('JOURNAL.TXT')
assert gpu['hardware_accepted'] is True and gpu['driver']=='panthor'
assert gpu['software_renderer'] is False and 'Mali-G610' in gpu['renderer']
assert gpu['pixel_rgba']==[64,128,191,255] and gpu['gl_error']==0 and gpu['offscreen_clear_verified']
assert all(not Path(s).name.lower().startswith('libmali') for s in gpu['loaded_libraries'])
assert 'Mesa 26.0.3' in gpu['version']
assert read('SYSSTATE.TXT').strip()=='running' and '0 loaded units listed.' in read('FAILED.TXT')
assert 'ActiveState=active' in read('TARGET.TXT')
assert 'connected\nenabled\n1200x1920' in read('DRM.TXT')
assert 'drivers/panthor' in read('DRM.TXT') and '200000000' in read('DRM.TXT')
assert all(s in read('GRAPHICS.TXT') for s in ['GPU_EXIT=0','WAYLAND_START=0','WAYLAND_STOP=0'])
assert read('GFXSTATE.TXT').count('Result=success')==2
assert 'type \'wayland\'' in journal
assert 'Console: switching to colour frame buffer device 150x120' in dmesg
assert 'fb0: rockchipdrmfb frame buffer device' in dmesg
assert '[drm] Initialized panthor' in dmesg
assert 'Linux version' not in read('KERNEL.TXT') # uname format, not boot text
assert '6.1.115-vendor-rk35xx' in read('KERNEL.TXT')
mounts={s.split()[1]:s.split() for s in read('MOUNTS.TXT').splitlines()}
assert mounts['/'][2]=='overlay' and mounts['/run'][2]=='tmpfs'
assert {'ro','norecovery'}<=set(mounts['/run/f8/container'][3].split(','))
assert mounts['/run/f8/lower'][2]=='squashfs' and 'ro' in mounts['/run/f8/lower'][3].split(',')
assert not re.search(r'Kernel panic|Oops:',dmesg)
report={'date':'2026-10-29','scope':'Official Armbian G2 real Panthor EGL pixel readback, DSI mode and observed bounded KWin Wayland window',
        'host_volume':'F: F8AG2','candidate_sha256':'6afe593ffcdbeb5c1dbef48dc97b25caece51ac5de6f00288db57eba854c0f08',
        'official_kernel':'6.1.115-vendor-rk35xx','gpu_result':gpu,
        'gpu_domain_fix_hardware_verified':True,'gpu_voltage_externally_measured':False,
        'dsi_mode':'1200x1920','test_gpu_frequency_hz':200000000,
        'wayland_session_created':True,'wayland_start_stop_success':True,
        'physical_test_window_user_confirmed':True,'physical_test_window_auto_closed_as_designed':True,
        'kwin_independent_renderer_log_captured':False,
        'framebuffer_console_registered':True,'screen_terminal_text_user_reported':True,
        'external_uart_tested':False,'root_writes_in_ram':True,'system_state':'running','failed_units':0,
        'touch_enabled':False,'touch_tested':False,'charging_tested':False,'full_plasma_sddm_tested':False,
        'stress_dvfs_suspend_tested':False,'panic_or_oops_in_snapshot':False,
        'snapshot_last_kernel_message_seconds':154.665116,
        'remaining_warnings':['VOP supply/DVFS fallback','panel bpc=0','extra overlay plane setup',
                              'RGA aggregate bind','early regulatory database load','AppArmor fusermount denials'],
        'note':'KWin output followed tty input rather than journald; next trial must explicitly capture compositor stdout/stderr',
        'files':[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
                 for f in sorted(logs.iterdir()) if f.suffix.upper() in ['.TXT','.JSON'] and f.name!='test-result.json']}
(logs/'test-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['gpu_domain_fix_hardware_verified','dsi_mode','physical_test_window_user_confirmed',
      'framebuffer_console_registered','system_state','touch_enabled','kwin_independent_renderer_log_captured']},ensure_ascii=False))
