"""Record the bounded results of the first real 6.1 diagnostic trial."""
import hashlib
import json
from pathlib import Path
import re

P=Path(__file__).resolve().parents[1]
logs=P/'local/hardware/armbian-6.1-firstboot-20261029-01'
kernel=(logs/'KERNEL.TXT').read_text()
dmesg=(logs/'DMESG.TXT').read_text()
parts=(logs/'PARTS.TXT').read_text()
devices=(logs/'DEVICES.TXT').read_text()
assert '6.1.172-f8-pro-armbian-eval' in kernel
assert 'F8 6.1 FIRSTBOOT INIT REACHED' in dmesg
assert all(re.search(r'\bmmcblk0p'+str(n)+r'\b',parts) for n in range(1,9))
assert 'fc000000.usb' in devices
files=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
       for p in sorted(logs.iterdir()) if p.is_file() and p.suffix.upper() in ['.TXT','.BIN']]
report={'scope':'First real minimal 6.1 kernel/USB/eMMC-enumeration trial; no desktop or full hardware acceptance',
 'date':'2026-10-29','source_directory':str(logs),'files':files,
 'candidate_sha256':'98037112b015172461c9eb776aba6b85acee8aa080ec74a08c8aba90dc49b496',
 'kernel_release_confirmed':'6.1.172-f8-pro-armbian-eval',
 'diagnostic_init_reached':True,'emmc_hs200_enumerated':True,'emmc_partitions_enumerated':8,
 'usb_udc':'fc000000.usb','host_log_volume_observed':'F: F861LOGS',
 'ramoops_registered':True,'ramoops_reset_persistence_tested':False,
 'panic_or_oops_in_captured_snapshot':bool(re.search(r'Kernel panic|Oops:',dmesg)),
 'rootfs_mount_or_storage_write_test_performed':False,'desktop_tested':False,'touch_tested':False,
 'cpu_dvfs_or_smp_tested':False,'full_hardware_passed':False,
 'runtime_memory_matches_observed_bank_layout':True,
 'loader_vs_static_memory_source_distinguished':False,
 'findings':[
  {'finding':'I2C0 GPIO0-11 conflicts with SPI2; original DT uses i2c0m2 GPIO0_D1/D2',
   'action':'Draft corrected to i2c0m2_xfer; not yet retested on hardware'},
  {'finding':'Big-core regulator/OPP setup fails and cpufreq defers',
   'action':'Recheck after I2C0 mux fix; cpufreq.off does not prevent vendor OPP probe'},
  {'finding':'No VOP available, RGA IOMMU bind error, no soundcards',
   'action':'Unrequested display/RGA/audio blocks need explicit diagnostic disable; not function tests'},
  {'finding':'Zero-size logo/LUT reserve warnings and initial console unavailable',
   'action':'Remove inactive diagnostic placeholders and wire a valid console before broader tests'},
  {'finding':'Regulator device-link warnings and optional RK806 power states missing',
   'action':'Audit before SMP/DVFS/suspend or charging tests'}]}
(logs/'test-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['kernel_release_confirmed','diagnostic_init_reached','emmc_partitions_enumerated',
 'host_log_volume_observed','panic_or_oops_in_captured_snapshot','full_hardware_passed']},ensure_ascii=False))
