"""Save a new bounded SSH test without overwriting previous evidence."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['stability','adc','fault','state','adc_audit'])
parser.add_argument('--sample-id',default='01',choices=[f'{x:02d}' for x in range(1,100)])
args=parser.parse_args()
out=P/'local/hardware/armbian-official-g6-r5-20261030-01'
path=out/(args.kind+'-'+args.sample_id+'.json');assert not path.exists(),'Preserve previous evidence'
if args.kind=='stability':script=P/'tools/read-f8-stability.sh'
elif args.kind=='state':script=P/'tools/read-f8-live-baseline.sh'
else:
    sourcefile={'adc':'bq-adc-oneshot.py','fault':'bq-fault-status.py','adc_audit':'bq-adc-audit.py'}[args.kind]
    source=(P/'armbian/power'/sourcefile).read_text()
    script=out/(args.kind+'-'+args.sample_id+'-runner.sh')
    assert not script.exists()
    script.write_text('set -eu\ntest "$(uname -r)" = 6.1.115-vendor-rk35xx\npython3 -I - <<\'F8_ADC_PY\'\n'+source+'\nF8_ADC_PY\n')
result=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227',
 '--script',str(script),'--sudo'],capture_output=True,text=True,timeout=85)
assert result.returncode==0,result.stderr[-1800:]
data=json.loads(result.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
if args.kind=='state':data['scope']='Fresh passive state after user reports displayed SOC100%'
baseline=json.loads((out/'ssh-before-charger.json').read_text())
data['same_boot_as_baseline']=data['boot_id']==baseline['boot_id']
with path.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
if args.kind=='stability':
    print(json.dumps({'same_boot':data['same_boot_as_baseline'],
      'samples':[{'uptime':s['uptime_seconds'],'cw_mv':s['power']['devices']['0x62']['decoded']['voltage_mv_reference_formula'],
        'soc':s['power']['devices']['0x62']['decoded']['soc_raw_percent'],'thermal_zones':s['thermal_zones']} for s in data['samples']],
      'kernel_alerts':data['kernel_alerts'],'failed':data['failed_units']['stdout'],'services':data['service_states']['stdout']},indent=2))
elif args.kind=='state':
    print(json.dumps({'same_boot':data['same_boot_as_baseline'],'uptime':data['uptime_seconds'],
      'power_age_seconds':data['power_age_seconds'],'bq':data['power']['devices']['0x6a']['decoded'],
      'cw':data['power']['devices']['0x62']['decoded'],'failed_units':data['failed_units']['stdout']},indent=2))
else:print(json.dumps(data,indent=2))
