"""Adapt the hardware-tested F8 DT to official Armbian GPU bindings; offline only.

F8 board wiring comes from R5. The GPU subtree comes verbatim from the signed
26.8.1 official DT, with provider phandles translated by physical node path.
This does not claim the older F8 DTS source was built by Armbian 26.8.1.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
E=P/'analysis/armbian/official-gpu-baseline-20261029'
O=P/'outputs/armbian/official-f8-graphics-r1b';O.mkdir(parents=True,exist_ok=True)
assert not (O/'dt-manifest.json').exists(), 'Preserve completed candidate'
board=P/'outputs/armbian/firstboot-diagnostic-r5/diagnostic.NOT-APPROVED.dtb'
reference=E/'reference-orangepi5-panthor-enabled.dtb'
assert hashlib.sha256(board.read_bytes()).hexdigest()=='542f003d3144bf21d6746904611e55675b30a5c8f97f08dfd09c2b0ebf81085c'
old=fdt(board.read_bytes());official=fdt(reference.read_bytes());nodes=copy.deepcopy(old)
def cells(data):
    assert len(data)%4==0
    return list(struct.unpack('>'+str(len(data)//4)+'I',data))
def packed(values):return struct.pack('>'+str(len(values))+'I',*values)
def handles(tree):return {cells(v['phandle'])[0]:k for k,v in tree.items() if 'phandle' in v}
oh=handles(official);bh=handles(nodes)
new_handle=max(bh)+1
gpu='/gpu-panthor@fb000000'
subtree={k:copy.deepcopy(v) for k,v in official.items() if k==gpu or k.startswith(gpu+'/')}
# Retain existing handles for existing node paths; allocate only for new paths.
translation={}
for number,path in oh.items():
    if path in nodes and 'phandle' in nodes[path]:
        translation[number]=cells(nodes[path]['phandle'])[0]
    elif path in subtree:
        translation[number]=new_handle;new_handle+=1
checks=[]
def translate_provider(data,cell_property):
    values=cells(data);out=[];index=0
    while index<len(values):
        handle=values[index];path=oh[handle]
        assert path in nodes and handle in translation, path
        count=cells(official[path][cell_property])[0]
        assert official[path][cell_property]==nodes[path][cell_property],path
        if 'reg' in official[path]:assert official[path]['reg']==nodes[path]['reg'],path
        args=values[index+1:index+1+count];assert len(args)==count
        out.extend([translation[handle],*args]);index+=count+1
        checks.append({'provider':path,'cell_property':cell_property,'argument_cells':args})
    return packed(out)
for path,props in subtree.items():
    for key,value in list(props.items()):
        if key in ['phandle','linux,phandle','operating-points-v2']:
            props[key]=packed([translation[cells(value)[0]]])
        elif key in ['clocks','assigned-clocks']:
            props[key]=translate_provider(value,'#clock-cells')
        elif key=='power-domains':props[key]=translate_provider(value,'#power-domain-cells')
        elif key.endswith('-supply'):
            handle=cells(value)[0];supply=oh[handle]
            assert supply.endswith('/regulators/DCDC_REG1'), supply
            props[key]=packed([translation[handle]])
            checks.append({'supply_path':supply})
# Bound initial rendering test to the official 200 MHz OPP; no custom voltage.
opp=gpu+'/opp-table'
retained=[]
for path,props in subtree.items():
    if path.startswith(opp+'/') and path.count('/')==opp.count('/')+1:
        hz=int.from_bytes(props['opp-hz'],'big')
        if hz==200000000:retained.append(path)
        else:props['status']=b'disabled\0'
assert len(retained)==1
rail=nodes['/spi@feb20000/rk806single@0/regulators/DCDC_REG1']
low=cells(rail['regulator-min-microvolt'])[0];high=cells(rail['regulator-max-microvolt'])[0]
assert all(low<=v<=high for v in cells(subtree[retained[0]]['opp-microvolt']))
for path in list(nodes):
    if path==gpu or path.startswith(gpu+'/'):del nodes[path]
nodes.update(subtree)
nodes['/gpu@fb000000']['status']=b'disabled\0'
nodes[gpu]['status']=b'okay\0'
# Route existing GPU thermal cooling references to the active DRM driver.
oldgpu=cells(nodes['/gpu@fb000000']['phandle'])[0]
newgpu=cells(nodes[gpu]['phandle'])[0]
for path,props in nodes.items():
    if path.startswith('/thermal-zones/') and 'cooling-device' in props:
        values=cells(props['cooling-device']);index=0
        while index<len(values):
            provider=bh.get(values[index]);assert provider is not None
            count=cells(old[provider]['#cooling-cells'])[0]
            if values[index]==oldgpu:values[index]=newgpu
            index+=count+1
        props['cooling-device']=packed(values)
enabled=['/display-subsystem','/display-subsystem/route/route-dsi0',
         '/vop@fdd90000','/iommu@fdd97e00','/dsi@fde20000',
         '/dsi@fde20000/panel@0','/vcc3v3-lcd0-n','/backlight','/pwm@febf0020']
for path in enabled:
    assert path in nodes,path
    nodes[path]['status']=b'okay\0'
nodes['/backlight']['default-brightness-level']=packed([32])
nodes['/']['model']=b'F8-PRO official Armbian GPU/display candidate R1\0'
nodes['/chosen']['bootargs']=old['/chosen']['bootargs']
# Serialize FDT directly so phandle properties are validated as DTB data rather
# than producing source-marker warnings for raw byte-array DTS properties.
children={k:[] for k in nodes}
for path in nodes:
    if path!='/':children[path.rsplit('/',1)[0] or '/'].append(path)
reservations=[]
data=board.read_bytes();reserve=struct.unpack_from('>I',data,16)[0]
while True:
    address,size=struct.unpack_from('>QQ',data,reserve);reserve+=16
    if address==size==0:break
    reservations.append((address,size))
strings=bytearray();offsets={};structure=bytearray()
def align4(value):return value+bytes((-len(value))%4)
def emit(path):
    name='' if path=='/' else path.rsplit('/',1)[1]
    structure.extend(packed([1])+align4(name.encode()+b'\0'))
    for key,value in nodes[path].items():
        if key not in offsets:
            offsets[key]=len(strings);strings.extend(key.encode()+b'\0')
        structure.extend(packed([3,len(value),offsets[key]])+align4(value))
    for child in children[path]:emit(child)
    structure.extend(packed([2]))
emit('/');structure.extend(packed([9]))
rsv=b''.join(struct.pack('>QQ',a,s) for a,s in [*reservations,(0,0)])
offstruct=40+len(rsv);offstrings=offstruct+len(structure)
header=packed([0xd00dfeed,offstrings+len(strings),offstruct,offstrings,40,17,16,
               struct.unpack_from('>I',data,28)[0],len(strings),len(structure)])
serialized=O/'f8-official-graphics-r1.input.dtb'
serialized.write_bytes(header+rsv+structure+strings)
assert fdt(serialized.read_bytes())==nodes
draft=O/'f8-official-graphics-r1.REVIEW.dts'
subprocess.run(['dtc','-I','dtb','-O','dts','-o',str(draft),str(serialized)],check=True,capture_output=True)
dtb=O/'f8-official-graphics-r1.NOT-APPROVED.dtb'
r=subprocess.run(['dtc','-I','dtb','-O','dtb','-o',str(dtb),str(serialized)],capture_output=True,text=True)
(O/'dtc.log').write_text(r.stderr);r.check_returncode()
checked=fdt(dtb.read_bytes());assert checked==nodes
assert checked['/gpu@fb000000']['status']==b'disabled\0'
assert checked[gpu]['status']==b'okay\0'
for path in ['/i2c@fd880000','/mmc@fe2e0000','/serial@feb50000']:
    assert checked[path]==old[path],path
timing='/dsi@fde20000/panel@0/display-timings/timing0'
assert checked[timing]==old[timing]
report={'scope':'Offline F8 board DT carried forward with official 26.8.1 GPU subtree and display enablement; not deployment approval',
        'board_input':str(board.relative_to(P)), 'board_input_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),
        'gpu_reference':str(reference.relative_to(P)), 'gpu_reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
        'output_sha256':hashlib.sha256(dtb.read_bytes()).hexdigest(),
        'output_bytes':dtb.stat().st_size,'provider_translation_checks':checks,
        'official_gpu_subtree_used':True,'initial_gpu_max_hz':200000000,
        'initial_gpu_voltage_from_official_opp':True,'display_nodes_enabled':enabled,
        'panel_timing_preserved':True,'backlight_initial_level':32,
        'board_i2c0_emmc_console_preserved':True,'roundtrip_bytes_verified':True,
        'binding_review_complete':False,'hardware_test_performed':False,
        'remaining':['Compare new dtc warnings to saved baseline','Audit official display driver/module configuration',
                     'Prepare official RAM-overlay root and matching filesystem modules',
                     'GPU/Mesa pixel-readback plus Wayland test service','FIT packaging and staged-root verification']}
(O/'dt-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='provider_translation_checks'},indent=2))
