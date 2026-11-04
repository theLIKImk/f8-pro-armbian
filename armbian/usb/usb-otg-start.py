"""Late USB startup for the verified U5 DT, isolated from desktop/SSH startup."""
import hashlib,json,subprocess,time
from pathlib import Path
dt=Path('/sys/firmware/devicetree/base')
trial=dt/'chosen/f8-usb-trial'
if not trial.exists() or trial.read_bytes()!=b'u5\0':
    print('USB OTG startup skipped: DT is outside the verified U5 profile')
    raise SystemExit(0)
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
assert (dt/'i2c@fec80000/charger@6a/compatible').read_bytes()==b'f8-pro,otg-vbus-only\0'
assert (dt/'syscon@fd5d0000/usb2-phy@0/otg-port/rockchip,sel-pipe-phystatus').exists()
assert any('fd5d0000' in p.name for p in Path('/sys/class/phy').glob('*'))
power=subprocess.check_output(['systemctl','show','f8-live-power.service','-p','ActiveState','-p','ConditionResult'],text=True)
assert 'ActiveState=inactive' in power and 'ConditionResult=no' in power
module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')
assert module.is_file() and not module.is_symlink()
assert hashlib.sha256(module.read_bytes()).hexdigest()=='a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c'
already=Path('/sys/module/f8_otg_vbus').exists()
if not already:subprocess.run(['insmod',str(module)],check=True,timeout=12)
expected={'6-0022':'typec_fusb302','6-006a':'f8-otg-vbus'}
deadline=time.monotonic()+6
while True:
    bindings={name:(Path('/sys/bus/i2c/devices')/name/'driver').resolve().name for name in expected}
    if bindings==expected:break
    assert time.monotonic()<deadline,bindings
    time.sleep(0.2)
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'profile':'u5','module_already_loaded':already,'bindings':bindings,'charger_policy_initialized':False}))
