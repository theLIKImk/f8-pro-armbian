import hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-desktop-t1r2-success-20261030-01'
out=dest/'native-acceptance-firstboot.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/verify-f8-native-desktop.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
data=json.loads(r.stdout);out.write_text(json.dumps(data,indent=2)+'\n')
mfile=P/'outputs/armbian/official-f8-desktop-t1r2/preflight.json';m=json.loads(mfile.read_text())
base=json.loads((dest/'nonbattery-baseline.json').read_text())
assert hashlib.sha256((base['handoff']+'\n').encode()).hexdigest()==m['dropin_sha256']
backup=mfile.with_name('preflight-before-hardware-verification.json')
if not backup.exists():backup.write_bytes(mfile.read_bytes())
m.update({'cold_boot_verified':True,'user_desktop_boot_confirmed':True,'runtime_handoff_hash_verified':True,
          'verified_boot_id':data['boot_id'],'hardware_evidence':str(out.relative_to(P)),
          'battery_work_deferred_by_user':True})
mfile.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(data,indent=2))
