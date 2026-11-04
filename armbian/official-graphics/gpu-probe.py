"""Require real Panthor, hardware EGL rendering and a verified pixel readback."""
import argparse
import ctypes as C
import importlib.util
import json
from pathlib import Path
import re

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
result={'hardware_accepted':False}
def render_device(m,device_path):
    """Mesa GBM may have no pbuffers; use a surfaceless GLES3 RGBA8 FBO."""
    import os
    P=C.c_void_p;I=C.c_int;U=C.c_uint
    egl=C.CDLL('libEGL.so.1');gbm=C.CDLL('libgbm.so.1')
    fd=os.open(device_path,os.O_RDWR|os.O_CLOEXEC)
    device=display=context=None;gl=None;frame=U();buffer=U();current=False;initialized=False
    try:
        device=m.function(gbm,'gbm_create_device',P,I)(fd)
        assert device,'GBM device creation failed'
        proc=m.function(egl,'eglGetProcAddress',P,C.c_char_p)(b'eglGetPlatformDisplayEXT')
        assert proc,'EGL platform display unavailable'
        display=C.CFUNCTYPE(P,U,P,P)(proc)(0x31D7,device,None)
        major=I();minor=I()
        assert m.function(egl,'eglInitialize',U,P,P,P)(display,C.byref(major),C.byref(minor)),'eglInitialize failed'
        initialized=True
        extensions=m.function(egl,'eglQueryString',C.c_char_p,P,I)(display,0x3055) or b''
        assert b'EGL_KHR_surfaceless_context' in extensions,'EGL surfaceless context unsupported'
        assert m.function(egl,'eglBindAPI',U,U)(0x30A0),'GLES API unavailable'
        config=P();count=I()
        attrs=m.array(0x3033,0,0x3040,0x40,0x3038)
        assert m.function(egl,'eglChooseConfig',U,P,P,P,I,P)(display,attrs,C.byref(config),1,C.byref(count)) and count.value,'No GLES3 EGL config'
        context=m.function(egl,'eglCreateContext',P,P,P,P,P)(display,config,None,m.array(0x3098,3,0x3038))
        assert context,'GLES3 context creation failed'
        assert m.function(egl,'eglMakeCurrent',U,P,P,P,P)(display,None,None,context),'Surfaceless eglMakeCurrent failed'
        current=True;gl=C.CDLL('libGLESv2.so.2')
        m.function(gl,'glGenFramebuffers',None,I,P)(1,C.byref(frame))
        m.function(gl,'glBindFramebuffer',None,U,U)(0x8D40,frame.value)
        m.function(gl,'glGenRenderbuffers',None,I,P)(1,C.byref(buffer))
        m.function(gl,'glBindRenderbuffer',None,U,U)(0x8D41,buffer.value)
        m.function(gl,'glRenderbufferStorage',None,U,U,I,I)(0x8D41,0x8058,16,16)
        m.function(gl,'glFramebufferRenderbuffer',None,U,U,U,U)(0x8D40,0x8CE0,0x8D41,buffer.value)
        assert m.function(gl,'glCheckFramebufferStatus',U,U)(0x8D40)==0x8CD5,'RGBA8 framebuffer incomplete'
        m.function(gl,'glViewport',None,I,I,I,I)(0,0,16,16)
        info=m.render(gl)
        info.update(egl_platform='gbm-surfaceless-fbo',drm_device=device_path,
                    egl_version=f'{major.value}.{minor.value}',framebuffer_format='RGBA8',framebuffer_size=[16,16])
        return info
    finally:
        if current and gl:
            if buffer.value:m.function(gl,'glDeleteRenderbuffers',None,I,P)(1,C.byref(buffer))
            if frame.value:m.function(gl,'glDeleteFramebuffers',None,I,P)(1,C.byref(frame))
        if initialized:
            m.function(egl,'eglMakeCurrent',U,P,P,P,P)(display,None,None,None)
            if context:m.function(egl,'eglDestroyContext',U,P,P)(display,context)
            m.function(egl,'eglTerminate',U,P)(display)
        if device:m.function(gbm,'gbm_device_destroy',None,P)(device)
        os.close(fd)
try:
    devices=[]
    for path in Path('/sys/class/drm').glob('renderD*'):
        driver=path/'device/driver'
        if driver.is_symlink() and driver.resolve().name=='panthor':devices.append(path.name)
    if len(devices)!=1:raise RuntimeError(f'Expected one Panthor render node, found {devices}')
    spec=importlib.util.spec_from_file_location('f8_egl_probe',Path(__file__).with_name('probe-gpu-context.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.EGL_PLATFORM='gbm'
    module.DRM_DEVICE='/dev/dri/'+devices[0]
    module.EGL_LIBRARY='libEGL.so.1';module.GLES_LIBRARY='libGLESv2.so.2';module.GBM_LIBRARY='libgbm.so.1'
    result.update(render_device(module,module.DRM_DEVICE))
    result['driver']='panthor'
    result['loaded_libraries']=sorted({s.split()[-1] for s in Path('/proc/self/maps').read_text().splitlines()
                                      if '/' in s and re.search(r'lib(?:EGL|GLES|GL|Mali|mali|gbm|gallium)|swrast',s)})
    assert result.get('offscreen_clear_verified') is True,'Pixel readback failed'
    assert result.get('software_renderer') is False,'Software renderer rejected'
    assert re.search(r'G610',result.get('renderer',''),re.I),'Unexpected GPU renderer'
    assert not any(Path(s).name.lower().startswith('libmali') for s in result['loaded_libraries']),'libMali rejected'
    result['hardware_accepted']=True
except Exception as error:
    result['error']=str(error)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['hardware_accepted'] else 1)
