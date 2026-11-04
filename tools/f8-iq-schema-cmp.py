import json

# 关键验证：GC5035 IQ 的 scene_isp21 内部 schema 与 OV8858 scene_isp30 是否同构
files = {
    'GC5035(scene_isp21)': '/opt/f8-pro-camera/aiq-v6-c4/iqfiles/gc5035_XHG-RKX11F-V5_HR232H65.json',
    'OV8858(scene_isp30)': '/opt/f8-pro-camera/aiq-v6-c4/iqfiles/ov8858_HS5885-BNSM1018-V01_default.json',
}
schemas = {}
for name, path in files.items():
    with open(path) as f:
        d = json.load(f)
    sub = d['main_scene'][0]['sub_scene'][0]
    scene_key = list(sub.keys())[0]
    scene = sub[scene_key]
    schemas[name] = set(scene.keys())
    print(f'{name}: scene key = {scene_key}, 段数量: {len(scene.keys())}')

a = schemas['GC5035(scene_isp21)']
b = schemas['OV8858(scene_isp30)']
print()
print('两者共有段数:', len(a & b))
print('GC5035 独有:', sorted(a - b))
print('OV8858 独有:', sorted(b - a))
print('MARKER_DONE')
