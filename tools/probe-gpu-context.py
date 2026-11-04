"""Ubuntu 20.04 standard-library GPU probe; one API per isolated process.

Creates only a 16x16 offscreen buffer; does not install or reconfigure drivers.
"""
import argparse
import ctypes as C
import ctypes.util
import json
import os
from pathlib import Path
import re

P = C.c_void_p
I = C.c_int
U = C.c_uint
INFO_ONLY = False
EGL_LIBRARY = GLES_LIBRARY = GBM_LIBRARY = None
EGL_PLATFORM = 'default'
DRM_DEVICE = '/dev/dri/card0'


def function(library, name, result, *arguments):
    value = getattr(library, name)
    value.restype, value.argtypes = result, list(arguments)
    return value


def array(*items):
    return (I * len(items))(*items)


def render(gl):
    get = function(gl, 'glGetString', C.c_char_p, U)
    result = {key: (get(code) or b'').decode('utf-8', 'replace')
              for key, code in [('vendor', 0x1F00), ('renderer', 0x1F01), ('version', 0x1F02)]}
    result['software_renderer'] = bool(re.search(r'llvmpipe|softpipe|lavapipe', result['renderer'], re.I))
    if INFO_ONLY:
        result['offscreen_clear_test'] = 'not_requested'
        return result
    function(gl, 'glClearColor', None, C.c_float, C.c_float, C.c_float, C.c_float)(0.25, 0.5, 0.75, 1.0)
    function(gl, 'glClear', None, U)(0x4000)
    pixel = (C.c_ubyte * 4)()
    function(gl, 'glReadPixels', None, I, I, I, I, U, U, P)(0, 0, 1, 1, 0x1908, 0x1401, pixel)
    function(gl, 'glFinish', None)()
    result['pixel_rgba'] = list(pixel)
    result['gl_error'] = function(gl, 'glGetError', U)()
    result['offscreen_clear_verified'] = result['gl_error'] == 0 and all(abs(a - b) <= 2 for a, b in zip(pixel, (64, 128, 191, 255)))
    return result


def egl():
    lib = C.CDLL(EGL_LIBRARY or ctypes.util.find_library('EGL') or 'libEGL.so.1')
    descriptor = None
    gbm = device = None
    try:
        if EGL_PLATFORM == 'gbm':
            descriptor = os.open(DRM_DEVICE, os.O_RDWR | os.O_CLOEXEC)
            gbm = C.CDLL(GBM_LIBRARY or ctypes.util.find_library('gbm') or 'libgbm.so.1')
            device = function(gbm, 'gbm_create_device', P, I)(descriptor)
            if not device:
                raise RuntimeError('gbm_create_device failed')
            address = function(lib, 'eglGetProcAddress', P, C.c_char_p)(b'eglGetPlatformDisplayEXT')
            if address:
                display = C.CFUNCTYPE(P, U, P, P)(address)(0x31D7, device, None)
            else:
                display = function(lib, 'eglGetPlatformDisplay', P, U, P, P)(0x31D7, device, None)
        else:
            display = function(lib, 'eglGetDisplay', P, P)(None)
        result = egl_context(lib, display)
        result['egl_platform'] = EGL_PLATFORM
        if EGL_PLATFORM == 'gbm':
            result['drm_device'] = DRM_DEVICE
        return result
    finally:
        if device:
            function(gbm, 'gbm_device_destroy', None, P)(device)
        if descriptor is not None:
            os.close(descriptor)


def egl_context(lib, display):
    major, minor = I(), I()
    if not function(lib, 'eglInitialize', U, P, P, P)(display, C.byref(major), C.byref(minor)):
        raise RuntimeError('eglInitialize failed: ' + hex(function(lib, 'eglGetError', U)()))
    surface = context = None
    try:
        assert function(lib, 'eglBindAPI', U, U)(0x30A0), 'eglBindAPI failed'
        configs, count = (P * 1)(), I()
        attrs = array(0x3033, 1, 0x3040, 4, 0x3024, 8, 0x3023, 8, 0x3022, 8, 0x3021, 8, 0x3038)
        assert function(lib, 'eglChooseConfig', U, P, P, P, I, P)(display, attrs, configs, 1, C.byref(count)) and count.value, 'No EGL pbuffer config'
        surface = function(lib, 'eglCreatePbufferSurface', P, P, P, P)(display, configs[0], array(0x3057, 16, 0x3056, 16, 0x3038))
        context = function(lib, 'eglCreateContext', P, P, P, P, P)(display, configs[0], None, array(0x3098, 2, 0x3038))
        assert surface and context, 'EGL pbuffer/context creation failed'
        assert function(lib, 'eglMakeCurrent', U, P, P, P, P)(display, surface, surface, context), 'eglMakeCurrent failed'
        result = render(C.CDLL(GLES_LIBRARY or ctypes.util.find_library('GLESv2') or 'libGLESv2.so.2'))
        result['egl_version'] = '{}.{}'.format(major.value, minor.value)
        return result
    finally:
        function(lib, 'eglMakeCurrent', U, P, P, P, P)(display, None, None, None)
        if context:
            function(lib, 'eglDestroyContext', U, P, P)(display, context)
        if surface:
            function(lib, 'eglDestroySurface', U, P, P)(display, surface)
        function(lib, 'eglTerminate', U, P)(display)


def glx():
    x = C.CDLL(ctypes.util.find_library('X11') or 'libX11.so.6')
    gl = C.CDLL(ctypes.util.find_library('GL') or 'libGL.so.1')
    display = function(x, 'XOpenDisplay', P, C.c_char_p)(None)
    assert display, 'XOpenDisplay failed'
    configs = None
    context = pbuffer = None
    try:
        screen = function(x, 'XDefaultScreen', I, P)(display)
        count = I()
        configs = function(gl, 'glXChooseFBConfig', C.POINTER(P), P, I, P, P)(display, screen,
                    array(0x8010, 4, 0x8011, 1, 8, 8, 9, 8, 10, 8, 11, 8, 5, 0, 0), C.byref(count))
        assert configs and count.value, 'No GLX pbuffer config'
        pbuffer = function(gl, 'glXCreatePbuffer', C.c_ulong, P, P, P)(display, configs[0], array(0x8041, 16, 0x8040, 16, 0))
        context = function(gl, 'glXCreateNewContext', P, P, P, I, P, I)(display, configs[0], 0x8014, None, 1)
        assert pbuffer and context, 'GLX pbuffer/context creation failed'
        assert function(gl, 'glXMakeContextCurrent', I, P, C.c_ulong, C.c_ulong, P)(display, pbuffer, pbuffer, context), 'glXMakeContextCurrent failed'
        result = render(gl)
        result['direct'] = bool(function(gl, 'glXIsDirect', I, P, P)(display, context))
        return result
    finally:
        function(gl, 'glXMakeContextCurrent', I, P, C.c_ulong, C.c_ulong, P)(display, 0, 0, None)
        if context:
            function(gl, 'glXDestroyContext', None, P, P)(display, context)
        if pbuffer:
            function(gl, 'glXDestroyPbuffer', None, P, C.c_ulong)(display, pbuffer)
        if configs:
            function(x, 'XFree', I, P)(configs)
        function(x, 'XCloseDisplay', I, P)(display)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('api', choices=('egl', 'glx'))
    parser.add_argument('--info-only', action='store_true', help='Query context strings without drawing')
    parser.add_argument('--output', type=Path, help='Write clean JSON separately from native-library stdout')
    parser.add_argument('--egl-library', help='Explicit private EGL library; does not change system configuration')
    parser.add_argument('--gles-library', help='Explicit private GLES library')
    parser.add_argument('--gbm-library', help='Explicit private GBM library')
    parser.add_argument('--egl-platform', choices=('default', 'gbm'), default='default')
    parser.add_argument('--drm-device', default='/dev/dri/card0')
    args = parser.parse_args()
    INFO_ONLY = args.info_only
    EGL_LIBRARY, GLES_LIBRARY, GBM_LIBRARY = args.egl_library, args.gles_library, args.gbm_library
    EGL_PLATFORM, DRM_DEVICE = args.egl_platform, args.drm_device
    try:
        result = {'api': args.api, **(egl() if args.api == 'egl' else glx())}
        result['loaded_libraries'] = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                                             if re.search(r'lib(?:EGL|GLES|GL|Mali|mali|gbm)|swrast', line) and '/' in line})
    except Exception as error:
        result = {'api': args.api, 'error': str(error)}
        if args.output:
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        raise SystemExit(1)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
