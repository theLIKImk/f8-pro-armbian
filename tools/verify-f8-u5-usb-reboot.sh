#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert boot!='9df01d2b-d624-4364-8d3d-a06ff6847720'
assert Path('/sys/firmware/devicetree/base/chosen/f8-usb-trial').read_bytes()==b'u5\0'
assert Path('/sys/module/f8_otg_vbus').exists()
assert not Path('/sys/module/f8_otg_status').exists()
expected={'6-0022':'typec_fusb302','6-006a':'f8-otg-vbus'}
bindings={name:(Path('/sys/bus/i2c/devices')/name/'driver').resolve().name for name in expected};assert bindings==expected
status=subprocess.check_output(['systemctl','show','f8-usb-otg.service','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus'],text=True)
assert 'ActiveState=active' in status and 'Result=success' in status and 'ExecMainStatus=0' in status
assert subprocess.check_output(['systemctl','is-enabled','f8-usb-otg.service'],text=True).strip()=='enabled'
for name,digest in {'/usr/libexec/f8-pro/usb-otg-start.py':'670b3e0ef5af346aadc212b6a27b801061903c2054cca3a7063a65c9552f70b0','/etc/systemd/system/f8-usb-otg.service':'0eb23f0357bca05c18fc02c1dce9280ea5d6faa05217e152d0fcc49e976a8fe2'}.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
session=json.loads(Path('/run/user/1601/f8-desktop/session.json').read_text());assert session['session_type']=='wayland'
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='f8_usb_otg_vbus')
assert not Path('/sys/class/typec/port0-partner').exists()
assert (reg/'state').read_text().strip()=='disabled'
journal=subprocess.check_output(['journalctl','-b','-u','f8-usb-otg.service','--no-pager','-o','cat'],text=True)
assert '"module_already_loaded": false' in journal, journal
failed=subprocess.check_output(['systemctl','--failed','--no-legend','--no-pager'],text=True)
assert not failed.strip(),failed
print(json.dumps({'boot_id':boot,'usb_service':status,'bindings':bindings,'module_loaded_automatically_by_service':True,'startup_file_hashes_match':True,'wayland_session':session,'vbus_state':(reg/'state').read_text().strip(),'failed_units':failed,'usb_service_journal':journal},indent=2))
PY
