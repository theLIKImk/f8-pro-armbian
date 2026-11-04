"""Refresh ADC on input power, then publish a coherent, quality-tagged snapshot."""
import argparse
import json
from pathlib import Path
import subprocess
import time

def merge_quality(data,adc,now):
    bq=data.get('devices',{}).get('0x6a',{})
    decoded=bq.get('decoded',{})
    decoded['actual_battery_current_ma']=None
    decoded['battery_current_channel_calibrated']=False
    decoded['adc_refreshed_by_sampler']=False
    decoded['battery_charge_current_ma_estimate']=None
    data['adc_refresh']={'attempted':adc is not None,'fresh':False,'charging_policy_writes':0}
    if adc is None:
        data['adc_refresh']['reason']='No external power or no confirmed PG; ADC left off'
        return data
    quality=data['adc_refresh'];quality['result_complete']=adc.get('complete',False)
    quality['conversion_handshake_verified']=adc.get('conversion_handshake_verified',False)
    quality['configuration_unchanged']=adc.get('configuration_unchanged',False)
    age=now-adc.get('conversion_completed_monotonic',-1e20)
    quality['age_seconds']=age if age>=0 else None
    post=adc.get('after_raw',{});raw=bq.get('raw',{})
    match=all(raw.get(hex(i))==post.get(hex(i)) and hex(i) in raw for i in range(14,19))
    input_present=bool(decoded.get('power_good')) and bool(post.get('0xb',0)&4) and bool(post.get('0x11',0)&128)
    valid=all([adc.get('complete'),quality['conversion_handshake_verified'],
               quality['configuration_unchanged'],0<=age<5,match,input_present])
    quality.update(raw_data_matches_conversion=match,input_still_present=input_present,fresh=valid)
    if valid:
        code=post['0x12']&127
        decoded.update(adc_refreshed_by_sampler=True,adc_sample_age_seconds=age,
          charge_current_raw_code=code,battery_charge_current_ma_estimate=code*50,
          linux_current_now_ua_estimate=-code*50000,
          current_interpretation='BQ25890-compatible scaling; not independently calibrated; zero code does not prove no charge',
          adc_note='Fresh single conversion with observed busy/clear and matching readback')
    else:
        quality['reason']='ADC failure, missing busy/clear, stale data, changed raw values or input transition'
        if 'error' in adc:quality['error']=adc['error']
    return data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    passive=output.with_name('power-passive-stage.json')
    def read():
        r=subprocess.run(['python3','-I','/usr/libexec/f8-pro/power-readonly.py','--output',str(passive)],
                         capture_output=True,text=True,timeout=6)
        if r.returncode:raise RuntimeError('Passive register capture failed')
        data=json.loads(passive.read_text())
        if not data['complete']:raise RuntimeError('Incomplete passive snapshot')
        return data
    data=read();adc=None
    if data['devices']['0x6a'].get('decoded',{}).get('power_good'):
        r=subprocess.run(['python3','-I','/usr/libexec/f8-pro/bq-adc-oneshot.py'],capture_output=True,text=True,timeout=7)
        try:adc=json.loads(r.stdout)
        except ValueError:adc={'complete':False,'error':'ADC helper did not return a report'}
        data=read()
    data=merge_quality(data,adc,time.monotonic())
    data['scope']='G6 coherent power snapshot; input-powered single ADC, no charger-policy management'
    temp=output.with_suffix('.refresh-tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(output)

if __name__=='__main__':main()
