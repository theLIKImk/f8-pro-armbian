"""Read-only physical F8 sensor backend, shared with observation reader conventions."""
import json,math,subprocess,time,datetime
from pathlib import Path
from sensor_fusion import flat_heading,magnetic_pose

def read_text(path):
    return path.read_text().strip()

def read_device(device):
    result={'device':str(device),'name':read_text(device/'name'),'raw':{},'scaled':{},'errors':[],
            'mount_matrix':{},'monotonic':time.monotonic(),'time':datetime.datetime.now().astimezone().isoformat()}
    for kind in ['accel','anglvel']:
        values=[];raw=[]
        try:
            scale=float(read_text(device/f'in_{kind}_scale'))
            for axis in 'xyz':raw.append(int(read_text(device/f'in_{kind}_{axis}_raw')))
            values=[n*scale for n in raw]
            result['raw'][kind]=raw;result['scaled'][kind]=values
        except (OSError,ValueError) as e:result['errors'].append(f'{kind}: {e}')
        f=device/f'in_{kind}_mount_matrix'
        if f.exists():
            try:result['mount_matrix'][kind]=read_text(f)
            except OSError:pass
    try:
        f=device/'in_temp_input'
        result['temperature_c']=float(read_text(f))/1000 if f.exists() else (float(read_text(device/'in_temp_raw'))+float(read_text(device/'in_temp_offset')))*float(read_text(device/'in_temp_scale'))/1000
    except (OSError,ValueError):pass
    return result

def example_matrix(device):
    candidates=[]
    try:
        p=subprocess.run(['udevadm','info','--query=property','--path='+str(device)],capture_output=True,text=True,timeout=2)
        candidates += [('udev安装矩阵',line.split('=',1)[1]) for line in p.stdout.splitlines() if line.startswith('ACCEL_MOUNT_MATRIX=')]
    except (OSError,subprocess.TimeoutExpired):pass
    try:candidates.append(('IIO安装矩阵',read_text(device/'in_accel_mount_matrix')))
    except OSError:pass
    for source,text in candidates:
        try:
            m=[[float(v) for v in row.split(',')] for row in text.split(';')]
            assert len(m)==3 and all(len(row)==3 for row in m)
            assert all(abs(sum(m[i][k]*m[j][k] for k in range(3))-(1 if i==j else 0))<1e-6 for i in range(3) for j in range(3))
            det=m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
            assert abs(det-1)<1e-6
            return m,source
        except (ValueError,AssertionError):pass
    return [[1,0,0],[0,1,0],[0,0,1]],'未取得有效安装矩阵，范例使用原始轴'

def read_magnet(device,accel):
    calibration=None;full=False
    try:
        c=json.loads((Path.home()/'.config/f8-pro/compass-calibration.json').read_text())
        assert c['version'] in [1,2,3] and max(c.get('spans_ut',[0]))<=250
        assert len(c['offset_ut'])==len(c['scale'])==3 and all(math.isfinite(v) for k in ['offset_ut','scale'] for v in c[k]) and all(.1<v<10 for v in c['scale'])
        calibration=c;full=c['version']==2 and 'field_radius_ut' in c
    except (OSError,ValueError,KeyError,TypeError,AssertionError):pass
    meta={'full_3d':full,'calibration_present':calibration is not None,'heading':None}
    try:
        values=[float(read_text(device/f'in_magn_{axis}_raw'))*float(read_text(device/f'in_magn_{axis}_scale'))*100 for axis in 'xyz']
        out={**meta,'measurement_valid':True,'monotonic':time.monotonic(),'raw_ut':values,'field':math.sqrt(sum(v*v for v in values)),'compass_note':'未校准，请打开指南针校准'}
        if calibration:
            corrected=[(values[i]-c['offset_ut'][i])*c['scale'][i] for i in range(3)];out['corrected_ut']=corrected
            flat=accel and accel[2]/max(1e-6,math.sqrt(sum(v*v for v in accel)))<-.92
            if full and accel:
                ab=[sum(row[i]*accel[i] for i in range(3)) for row in ((0,-1,0),(-1,0,0),(0,0,-1))]
                mp=magnetic_pose(ab,corrected)
                if mp:out['heading']=mp['heading'];out['compass_note']='三轴校准 · 倾斜补偿'
                else:out['compass_note']='磁场异常或水平分量不足'
            elif not flat:out['compass_note']='平面校准仅支持屏幕朝上平放'
            elif math.hypot(corrected[0],corrected[1])>200:out['compass_note']='磁场干扰较强，请移开磁吸物品'
            else:out['heading']=flat_heading(corrected);out['compass_note']='平面校准，方向已调转180°'
        return out
    except (OSError,ValueError) as e:return {**meta,'measurement_valid':False,'compass_note':'磁场读数暂不可用','error':str(e)}
