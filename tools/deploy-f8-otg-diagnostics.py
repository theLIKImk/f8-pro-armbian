"""RAM-only OTG module replacement at an unplugged port; restore on failure."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=['01','02'],default='01');args=parser.parse_args()
base=P/'outputs/armbian/official-f8-usb-u1-module-diag';meta=json.loads((base/'module-check.json').read_text())
assert meta['all_import_crcs_match_actual_official_kernel']
blob=(base/meta['module']).read_bytes();assert hashlib.sha256(blob).hexdigest()==meta['sha256']
dest=P/'local/hardware/armbian-native-usb-20261101/u4r1';out=dest/('diag-deploy'+args.attempt+'.json');runner=dest/('diag-deploy'+args.attempt+'-runner.sh')
assert not out.exists() and not runner.exists()
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='d83ba29d-2d56-4a09-8240-2bee4bf10466'
assert not Path('/sys/class/typec/port0-partner').exists(), 'Unplug the tablet USB port first'
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='f8_usb_otg_vbus')
assert (reg/'state').read_text().strip()=='disabled' and (reg/'num_users').read_text().strip()=='0'
assert Path('/sys/module/f8_otg_vbus').exists()
old=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c'
stage=Path('/var/lib/f8-pro/usb-u4r1-diag-deploy01');stage.mkdir(exist_ok=False)
ram=Path('/run/f8/usb-u4r1-diag01');ram.mkdir(exist_ok=False)
module=ram/'f8_otg_vbus.ko';data=base64.b64decode(PAYLOAD)
assert hashlib.sha256(data).hexdigest()==DIGEST;module.write_bytes(data);module.chmod(0o600)
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    d={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    if p.returncode:raise RuntimeError(str(d))
    return d
tcpc=Path('/sys/bus/i2c/drivers/typec_fusb302')
device=Path('/sys/bus/i2c/devices/6-0022')
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'module_sha256':DIGEST,'port_unplugged_verified':True,'vbus_disabled_verified':True,'module_stored_in_ram_only':True,'diagnostic_reads':'REG00/02/03/07/0A/0B/11/14 only, no ADC start and no fault latch read'}
def save(): (stage/'result.json').write_text(json.dumps(result,indent=2)+'\\n')
def bind():
    if not (device/'driver').exists():(tcpc/'bind').write_text('6-0022')
save()
removed=False
try:
    (tcpc/'unbind').write_text('6-0022')
    result['remove_original']=cmd(['rmmod','f8_otg_vbus']);removed=True;save()
    result['load_diagnostic']=cmd(['insmod',str(module)]);save()
    bind();time.sleep(1)
    status=Path('/sys/bus/i2c/devices/6-006a/usb_status')
    result['passive_status_unplugged']=status.read_text().strip()
    result['fusb_bound']=str((device/'driver').resolve())
    result['success']=True
except Exception as error:
    result['error']=str(error)
    try:
        if (device/'driver').exists():(tcpc/'unbind').write_text('6-0022')
        if removed and Path('/sys/module/f8_otg_vbus').exists():cmd(['rmmod','f8_otg_vbus'])
        if not Path('/sys/module/f8_otg_vbus').exists():cmd(['insmod',str(old)])
        bind();result['original_restored']=True
    except Exception as rollback:result['restore_error']=str(rollback)
    result['success']=False
finally:
    save()
    subprocess.run(['journalctl','--sync'],capture_output=True,timeout=15)
print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(base64.b64encode(blob).decode())).replace('DIGEST',repr(meta['sha256'])).replace('diag-deploy01','diag-deploy'+args.attempt).replace('usb-u4r1-diag01','usb-u4r1-diag'+args.attempt)
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
if r.returncode:
    out.with_suffix('.ssh-error.txt').write_text(r.stderr[-3000:]);raise RuntimeError(r.stderr[-1600:])
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
