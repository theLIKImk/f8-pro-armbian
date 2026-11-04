"""Compare the failed KWin shader with an undefined-extension-macro guard."""
import ctypes as C
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gpu',ROOT/'probe-gpu-context.py')
gpu=importlib.util.module_from_spec(spec);spec.loader.exec_module(gpu)
prefix='/opt/f8-pro/vendor-gpu-g13p0-20261028/lib/'
gpu.EGL_LIBRARY=prefix+'libEGL.so.1'
gpu.GLES_LIBRARY=prefix+'libGLESv2.so.2'
gpu.GBM_LIBRARY=prefix+'libgbm.so.1'
gpu.EGL_PLATFORM='gbm'


def compare(gl):
    get=gpu.function(gl,'glGetString',C.c_char_p,gpu.U)
    renderer=(get(0x1F01) or b'').decode()
    assert 'Mali-G610' in renderer
    original=(ROOT/'failed.frag').read_bytes()
    old=b'#if GL_OES_standard_derivatives && TRAIT_ROUNDED_CORNERS && TRAIT_BORDER'
    new=b'#if defined(GL_OES_standard_derivatives) && TRAIT_ROUNDED_CORNERS && TRAIT_BORDER'
    assert original.count(old)==1
    results={}
    for name,source in [('original',original),('defined_guard',original.replace(old,new))]:
        shader=gpu.function(gl,'glCreateShader',gpu.U,gpu.U)(0x8B30)
        try:
            pointer=C.c_char_p(source)
            gpu.function(gl,'glShaderSource',None,gpu.U,gpu.I,gpu.P,gpu.P)(shader,1,C.byref(pointer),None)
            gpu.function(gl,'glCompileShader',None,gpu.U)(shader)
            status=gpu.I();length=gpu.I()
            query=gpu.function(gl,'glGetShaderiv',None,gpu.U,gpu.U,gpu.P)
            query(shader,0x8B81,C.byref(status));query(shader,0x8B84,C.byref(length))
            buffer=C.create_string_buffer(max(length.value,1))
            gpu.function(gl,'glGetShaderInfoLog',None,gpu.U,gpu.I,gpu.P,gpu.P)(shader,len(buffer),None,buffer)
            results[name]={'compiled':bool(status.value),'log':buffer.value.decode(errors='replace')}
        finally:
            gpu.function(gl,'glDeleteShader',None,gpu.U)(shader)
    return {'renderer':renderer,'shader_comparison':results}


gpu.render=compare
result=gpu.egl()
result['guard_fix_verified']=not result['shader_comparison']['original']['compiled'] and result['shader_comparison']['defined_guard']['compiled']
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['guard_fix_verified'] else 3)
