import json

a = json.load(open('/opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json'))
b = json.load(open('/opt/f8-pro-camera/aiq-v6-c4/iqfiles/ov8858_HS5885-BNSM1018-V01_default.json'))

sa = set(a['main_scene'][0]['sub_scene'][0]['scene_isp21'].keys())
sb = set(b['main_scene'][0]['sub_scene'][0]['scene_isp30'].keys())

print('GC5035 scene_isp21 段:', sorted(sa))
print()
print('OV8858 scene_isp30 段:', sorted(sb))
print()
print('共同:', sorted(sa & sb))
print('GC独有(ISP21旧段):', sorted(sa - sb))
print('OV独有(ISP30新段):', sorted(sb - sa))
