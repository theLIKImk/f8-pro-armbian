/* Test-scoped bridge from the EGL 1.5 symbol to EGL_EXT_platform_base.
 * Does not change the driver's reported EGL version or advertise extensions.
 */
#define _GNU_SOURCE
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <dlfcn.h>
#include <limits.h>
#include <pthread.h>
#include <stdio.h>

static pthread_once_t once = PTHREAD_ONCE_INIT;
static PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC create_ext;
static PFNEGLGETERRORPROC driver_error;
static PFNEGLGETPLATFORMDISPLAYEXTPROC display_ext;
static PFNEGLINITIALIZEPROC driver_initialize;
static _Thread_local EGLint pending_error = EGL_SUCCESS;

static void initialize(void)
{
    create_ext = (PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC)
        eglGetProcAddress("eglCreatePlatformWindowSurfaceEXT");
    driver_error = (PFNEGLGETERRORPROC)dlsym(RTLD_NEXT, "eglGetError");
    display_ext = (PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
    driver_initialize = (PFNEGLINITIALIZEPROC)dlsym(RTLD_NEXT, "eglInitialize");
}

/* Qt's test requests no platform-display attributes. Keep this narrow. */
EGLAPI EGLDisplay EGLAPIENTRY eglGetPlatformDisplay(EGLenum platform, void *native, const EGLAttrib *attributes)
{
    pthread_once(&once, initialize);
    if (!display_ext || (attributes && attributes[0] != EGL_NONE)) {
        pending_error = EGL_BAD_ATTRIBUTE;
        return EGL_NO_DISPLAY;
    }
    EGLDisplay display = display_ext(platform, native, NULL);
    fprintf(stderr, "F8_EGL_BRIDGE platform=0x%x display=%s\n", platform,
            display != EGL_NO_DISPLAY ? "created" : "failed");
    return display;
}

EGLAPI EGLBoolean EGLAPIENTRY eglInitialize(EGLDisplay display, EGLint *major, EGLint *minor)
{
    pthread_once(&once, initialize);
    EGLBoolean ok = driver_initialize ? driver_initialize(display, major, minor) : EGL_FALSE;
    if (!ok)
        pending_error = driver_error ? driver_error() : EGL_NOT_INITIALIZED;
    fprintf(stderr, "F8_EGL_BRIDGE initialize=%d error=0x%x\n", ok, pending_error);
    return ok;
}

EGLAPI EGLint EGLAPIENTRY eglGetError(void)
{
    pthread_once(&once, initialize);
    if (pending_error != EGL_SUCCESS) {
        EGLint error = pending_error;
        pending_error = EGL_SUCCESS;
        if (driver_error)
            driver_error();
        return error;
    }
    return driver_error ? driver_error() : EGL_NOT_INITIALIZED;
}

EGLAPI EGLSurface EGLAPIENTRY eglCreatePlatformWindowSurface(
    EGLDisplay display, EGLConfig config, void *window, const EGLAttrib *attributes)
{
    EGLint converted[129];
    const EGLint *list = NULL;
    pthread_once(&once, initialize);
    if (!create_ext) {
        pending_error = EGL_BAD_ACCESS;
        fprintf(stderr, "F8_EGL_BRIDGE missing EXT entry point\n");
        return EGL_NO_SURFACE;
    }
    if (attributes) {
        unsigned i;
        for (i = 0; i < 128; i += 2) {
            if (attributes[i] == EGL_NONE) {
                converted[i] = EGL_NONE;
                list = converted;
                break;
            }
            if (attributes[i] < INT_MIN || attributes[i] > INT_MAX ||
                attributes[i+1] < INT_MIN || attributes[i+1] > INT_MAX) {
                pending_error = EGL_BAD_ATTRIBUTE;
                return EGL_NO_SURFACE;
            }
            converted[i] = (EGLint)attributes[i];
            converted[i+1] = (EGLint)attributes[i+1];
        }
        if (!list) {
            pending_error = EGL_BAD_ATTRIBUTE;
            return EGL_NO_SURFACE;
        }
    }
    EGLSurface surface = create_ext(display, config, window, list);
    if (surface == EGL_NO_SURFACE)
        pending_error = EGL_SUCCESS; /* Most recent failure belongs to driver. */
    fprintf(stderr, "F8_EGL_BRIDGE EXT surface=%s\n", surface != EGL_NO_SURFACE ? "created" : "failed");
    return surface;
}
