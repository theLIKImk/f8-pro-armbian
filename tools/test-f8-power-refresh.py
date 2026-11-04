"""Reject stale, inconsistent or unconfirmed current while accepting fresh samples."""
import copy
import importlib.util
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('refresh',P/'armbian/official-graphics/power-refresh.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
raw={hex(i):0 for i in range(14,19)};raw.update({'0xb':22,'0x11':149,'0x12':4})
data={'devices':{'0x6a':{'decoded':{'power_good':True},'raw':copy.deepcopy(raw)}}}
adc={'complete':True,'conversion_handshake_verified':True,'configuration_unchanged':True,
 'conversion_completed_monotonic':100,'after_raw':raw}
r=m.merge_quality(copy.deepcopy(data),copy.deepcopy(adc),101)
assert r['adc_refresh']['fresh'] and r['devices']['0x6a']['decoded']['battery_charge_current_ma_estimate']==200
assert r['devices']['0x6a']['decoded']['actual_battery_current_ma'] is None
cases=[]
for key in ['complete','conversion_handshake_verified','configuration_unchanged']:
    a=copy.deepcopy(adc);a[key]=False;cases.append((copy.deepcopy(data),a,101))
cases.append((copy.deepcopy(data),copy.deepcopy(adc),110))
cases.append((copy.deepcopy(data),None,101))
d=copy.deepcopy(data);d['devices']['0x6a']['raw']['0x12']=0;cases.append((d,copy.deepcopy(adc),101))
d=copy.deepcopy(data);d['devices']['0x6a']['decoded']['power_good']=False;cases.append((d,copy.deepcopy(adc),101))
for d,a,t in cases:
    result=m.merge_quality(d,a,t)
    assert not result['adc_refresh']['fresh']
    assert result['devices']['0x6a']['decoded']['battery_charge_current_ma_estimate'] is None
report={'passed':True,'fresh_sample_estimate_and_sign_verified':True,
 'rejected_cases':['incomplete','no_busy_handshake','configuration_changed','stale','no_input','different_raw_data','input_removed'],
 'never_claims_calibrated_actual_current':True}
(P/'analysis/armbian/live-g6/power-refresh-fixtures.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
