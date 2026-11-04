"""Summarize the saved R2 hardware snapshot without accessing the device."""
import hashlib
import json
from pathlib import Path
import re

P=Path(__file__).resolve().parents[1]
logs=P/'local/hardware/armbian-6.1-r2-20261029-01'
def read(name):return (logs/name).read_text()
dmesg=read('DMESG.TXT');pins=read('PINMUX.TXT');rails=read('CPURAILS.TXT');regulators=read('REGULATR.TXT')
assert '6.1.172-f8-pro-armbian-eval' in read('KERNEL.TXT')
assert 'secondboot regulator diagnostic R2' in read('MODEL.TXT')
assert 'F8 R2 REGULATOR SNAPSHOT COMPLETE' in dmesg
assert 'initcall rockchip_cpufreq_driver_init blacklisted' in dmesg
assert read('CPUONLINE.TXT').strip()=='0'
assert 'No such file or directory' in read('CPUFREQ.TXT')
assert 'already requested' not in dmesg and 'Error applying setting' not in dmesg
for pin in [25,26]:
    assert re.search(r'pin '+str(pin)+r' \(gpio0-'+str(pin)+r'\): fd880000.i2c .*group i2c0m2-xfer',pins)
values=[]
for index,address in enumerate(['0042','0043']):
    assert re.search(r'0-'+address+r'/driver ->[^\n]*rk860-regulator',rails)
    match=re.search(r'^\s+vdd_cpu_big'+str(index)+r'_s0\s+\d+\s+\d+\s+\d+\s+\S+\s+(\d+)mV',regulators,re.M)
    assert match
    values.append({'i2c_client':'0-'+address,'driver':'rk860-regulator',
                   'rail':'vdd_cpu_big'+str(index)+'_s0','driver_reported_mv':int(match[1]),
                   'external_voltage_measurement_performed':False})
manifest=json.loads((P/'outputs/armbian/firstboot-diagnostic-r2/manifest.json').read_text())
files=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
       for p in sorted(logs.iterdir()) if p.is_file() and p.suffix.upper() in ['.TXT','.BIN']]
report={'scope':'R2 real hardware regulator binding/pinmux/blacklist check, not DVFS/SMP/charging/desktop acceptance',
 'date':'2026-10-29','source_directory':str(logs),'files':files,
 'candidate_sha256':manifest['image_sha256'],'kernel_release_confirmed':manifest['release'],
 'r2_snapshot_complete':True,'host_volume_observed':'F: F861R2','i2c0_mux_conflict_absent_in_snapshot':True,
 'i2c0_gpio_pins':[25,26],'i2c0_mux_group':'i2c0m2-xfer','regulators':values,
 'vendor_cpufreq_initcall_skipped':True,'online_cpus':'0','cpufreq_policy_directory_absent':True,
 'display_missing_vop_error_absent': 'No available vop' not in dmesg,
 'zero_size_logo_lut_reserve_errors_absent':not bool(re.search(r'failed to reserve.*drm-(logo|cubic)',dmesg)),
 'panic_or_oops_in_snapshot':bool(re.search(r'Kernel panic|Oops:',dmesg)),
 'remaining_findings':['regulator device-link -ENOENT warnings remain despite successful binding',
                       'RGA aggregate bind error remains despite disabled cores',
                       'Initial console unavailable; other optional supply/firmware diagnostics remain'],
 'dvfs_tested':False,'smp_tested':False,'charging_tested':False,'desktop_tested':False,
 'rootfs_mount_tested':False,'rollback_completion_confirmed':False,'all_hardware_passed':False}
(logs/'test-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['i2c0_mux_conflict_absent_in_snapshot','regulators',
 'vendor_cpufreq_initcall_skipped','online_cpus','panic_or_oops_in_snapshot']},ensure_ascii=False,indent=2))
