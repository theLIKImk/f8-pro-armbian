"""Build a documented development profile, never relabel another sensor's IQ."""
import copy,hashlib,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
factory=Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging/etc/iqfiles')
front=factory/'gc5035_XHG-RKX11F-V5_HR232H65.json'
back=factory/'ov8858_HS5885-BNSM1018-V01_default.json'
original=json.loads(front.read_text());schema=json.loads(back.read_text())
result=copy.deepcopy(original);records=[]
new_blocks={'amerge_calib_v11','adrc_calib_v11','bayer2dnr_v2','bayertnr_v2','ynr_v3','cnr_v2','sharp_v4','cac_v03','cac_v10','af_v30','afec','gain_v2'}
def disable(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k.lower() in ('enable','enabled') or k.lower().endswith('_enable') or k.lower().endswith('_en'):obj[k]=0
            else:disable(v)
    elif isinstance(obj,list):
        for v in obj:disable(v)
for mi,main in enumerate(result['main_scene']):
 for si,sub in enumerate(main['sub_scene']):
    old=sub.pop('scene_isp21');base=schema['main_scene'][mi]['sub_scene'][si]['scene_isp30']
    shared=set(base)&set(old);out={k:copy.deepcopy(old[k]) for k in shared}
    assert set(base)-shared==new_blocks|{'agamma_calib_v11'}
    for k in new_blocks:
        out[k]=copy.deepcopy(base[k]);disable(out[k])
    # AF is not enabled on this fixed-focus front camera.
    out['af_v30']['TuningPara']['af_mode']='CalibDbV2_AFMODE_FIXED'
    # Hardware-independent gamma 2.2; log49 abscissae, not OV8858 color calibration.
    x=list(range(9))
    for step in [2,4,8,16,32,64,128]:x += [x[-1]+step*i for i in range(1,5)]
    x += list(range(1280,4097,256));x[-1]=4095
    assert len(x)==49 and x==sorted(x)
    gamma=[round(4095*(v/4095)**(1/2.2)) for v in x]
    reference=base['agamma_calib_v11']['GammaTuningPara']['Gamma_curve']
    assert max(abs(a-b) for a,b in zip(gamma,reference))<=2
    out['agamma_calib_v11']={'GammaTuningPara':{'Gamma_en':1,'Gamma_out_offset':0,'Gamma_curve':gamma}}
    out['ae_calib']['CommCtrl']['AecFrameRateMode']={'isFpsFix':1,'FpsValue':14}
    # ISP21 stores half-width/height sector sizes; ISP30 needs all 16.
    # Mirror geometry only. Keep the genuine 17x17 GC5035 gain tables intact.
    for resolution in out['lsc_v2']['common']['resolutionAll']:
        w,h=map(int,resolution['name'].split('x'))
        for key,extent in [('lsc_sect_size_x',w),('lsc_sect_size_y',h)]:
            half=resolution[key];assert len(half)==8 and sum(half)*2==extent and all(v>0 for v in half)
            resolution[key]=half+list(reversed(half));assert sum(resolution[key])==extent
    assert out['lsc_v2']['tbl']==old['lsc_v2']['tbl']
    sub['scene_isp30']=out
    records.append({'scene':[mi,si],'gc5035_shared_modules':sorted(shared),'disabled_schema_only_modules':sorted(new_blocks),'gamma':'generic gamma2.2/log49','fps':14})
assert result['sensor_calib']==original['sensor_calib'] and result['module_calib']==original['module_calib']
folder=P/'outputs/armbian/camera-front-c4-trial02';folder.mkdir(exist_ok=True)
dest=folder/front.name;assert not dest.exists()
dest.write_text(json.dumps(result,indent=2)+'\n')
manifest={'status':'DEVELOPMENT PROFILE, not production ISP30 tuning','factory_front_sha256':hashlib.sha256(front.read_bytes()).hexdigest(),'isp30_schema_source_sha256':hashlib.sha256(back.read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'sensor_and_module_calibration_preserved':True,'scenes':records,'noise_reduction_sharpening_drc_af_disabled':True}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
