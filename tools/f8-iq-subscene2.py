import json
d = json.load(open('/opt/f8-pro-camera/aiq-v6-c4/iqfiles/ov8858_HS5885-BNSM1018-V01_default.json'))
sub = d['main_scene'][0]['sub_scene'][0]
print('ov8858 sub_scene keys:', list(sub.keys()))
for k in sub:
    v = sub[k]
    print(' ', k, type(v).__name__, (list(v.keys())[:10] if isinstance(v, dict) else ''))
