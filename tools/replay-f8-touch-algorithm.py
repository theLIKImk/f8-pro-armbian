"""Replay captured firmware packets through the actual retained GSL C algorithm.
Runs offline only. Candidate thresholds are comparisons, never device writes.
"""
import argparse,collections,ctypes,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);a=p.parse_args()
outer=json.loads(a.trace.read_text());data=json.loads(outer['stdout']);assert data['algorithm_input']
rows=[]
for l in data['algorithm_input'].splitlines():
 m=re.search(r'\s(\d+\.\d+):\s+raw:.*?count=(\d+) x=\{([^}]+)\} y=\{([^}]+)\} ids=\{([^}]+)\}',l)
 if m:rows.append({'t':float(m[1]),'count':int(m[2]),**{key:[int(v.strip(),0) for v in m[i].split(',')] for key,i in [('x',3),('y',4),('id',5)]}})
assert rows,'No probe records parsed'
W=Path('/var/tmp/f8-pro-armbian/touch-replay-r3');W.mkdir(parents=True,exist_ok=True)
S=P/'armbian/touch/official-6.1.115-f8'
src=(S/'gsl_point_id.c').read_text()
src='int f8_input_count,f8_after_repeat,f8_masked,f8_pre_report;\n'+src
anchor='\tPointRepeat();\n\tGetPointNum(point_now);'
assert src.count(anchor)==1
src=src.replace(anchor,'\tf8_input_count=point_num;\n\tPointRepeat();\n\tGetPointNum(point_now);\n\tf8_after_repeat=point_num;')
src=src.replace('static void PointReport(struct gsl_touch_info *cinfo)\n{','static void PointReport(struct gsl_touch_info *cinfo)\n{\n f8_pre_report=point_num; f8_masked=(point_num > point_num_max && global_flag.other.over_report_mask != 0);')
(W/'algorithm.c').write_text(src)
subprocess.run(['gcc','-O2','-fPIC','-shared','-fwrapv','-fno-strict-aliasing','-I'+str(S),str(W/'algorithm.c'),'-o',str(W/'algorithm.so')],check=True)
lib=ctypes.CDLL(str(W/'algorithm.so'))
class Info(ctypes.Structure):_fields_=[('x',ctypes.c_int*10),('y',ctypes.c_int*10),('id',ctypes.c_int*10),('finger_num',ctypes.c_int)]
assert ctypes.sizeof(Info)==124
lib.gsl_DataInit.argtypes=[ctypes.POINTER(ctypes.c_uint)];lib.gsl_alg_id_main.argtypes=[ctypes.POINTER(Info)]
h=(S/'f8-pro-r8-shuping-reference.h').read_text().split('static unsigned int f8_pro_r8_shuping_algorithm[] = {',1)[1].split('};',1)[0]
values=[int(v,0) for v in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b',h)];assert len(values)==512
result={'rows':len(rows),'trace_header':data['algorithm_input'].splitlines()[:6],'profile':data['probe_profile'],'candidates':{}}
for label,repeat in [('baseline',None),('merge16_24',(16<<16)|24),('merge8_16',(8<<16)|16),('merge1_1',(1<<16)|1),('t2_delay1',0x00100018),('t2_delay1_no_frame_mask',0x00100018)]:
 conf=(ctypes.c_uint*512)(*values)
 if repeat is not None:conf[0x18]=repeat
 if label.startswith('t2_'):
  for n in range(2,10):conf[0x28]=(conf[0x28]&~(7<<(3*n)))|(1<<(3*n))
 if label.endswith('no_frame_mask'):conf[0x10]&=~1
 lib.gsl_DataInit(conf)
 counts=collections.Counter();repeat_losses=[];outputs=[];masked=0
 for r in rows:
  c=Info();c.finger_num=ctypes.c_int(r['count']).value
  for name in ['x','y','id']:
   for i,v in enumerate(r[name]):getattr(c,name)[i]=v
  lib.gsl_alg_id_main(ctypes.byref(c))
  masked+=ctypes.c_int.in_dll(lib,'f8_masked').value
  before=ctypes.c_int.in_dll(lib,'f8_input_count').value;after=ctypes.c_int.in_dll(lib,'f8_after_repeat').value
  counts[(r['count']&255,c.finger_num)]+=1
  if before>after:repeat_losses.append({'t':r['t'],'raw':r['count']&255,'before_repeat':before,'after_repeat':after,'output':c.finger_num})
  outputs.append({'t':r['t'],'raw':r['count']&255,'after_repeat':after,'output':c.finger_num,'points':[{'id':c.id[i],'x':c.x[i],'y':c.y[i]} for i in range(max(0,min(10,c.finger_num)))]})
 result['candidates'][label]={'repeat_config':hex(conf[0x18]),'report_delay_config':hex(conf[0x28]),'flags_config':hex(conf[0x10]),'raw_output_count_pairs':{f'{k[0]}->{k[1]}':v for k,v in sorted(counts.items())},'whole_frame_masked':masked,'repeat_merges':len(repeat_losses),'first_merges':repeat_losses[:12]}
 (W/(label+'-output.json')).write_text(json.dumps(outputs))
dest=a.trace.with_name(a.trace.stem+'-replay.json');dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
