import json
d = json.load(open('/opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json'))
sub = d['main_scene'][0]['sub_scene'][0]
print('sub_scene keys:', list(sub.keys()))
for k in sub:
    v = sub[k]
    print(' ', k, type(v).__name__, (list(v.keys())[:8] if isinstance(v, dict) else ''))
