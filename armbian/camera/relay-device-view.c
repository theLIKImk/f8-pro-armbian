/* Process-local compatibility view: consumers only open the real loopback node.
 * Reject physical video/subdev discovery; never invent devices or image data.
 * This is not a security boundary and is never loaded into the AIQ/capture worker.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
static int denied(const char *path) {
    if(!path)return 0;
    char resolved[4096];const char *p=realpath(path,resolved);
    if(!p)p=path;
    if(!strncmp(p,"/dev/video",10) || !strncmp(p,"/dev/v4l-subdev",15)) {
        if(strcmp(p,"/dev/video42")){errno=EACCES;return 1;}
    }
    return 0;
}
static int has_mode(int flags) {return (flags&O_CREAT) || ((flags&O_TMPFILE)==O_TMPFILE);}
#define OPEN_WRAPPER(name) \
int name(const char *path,int flags,...) { \
    if(denied(path))return -1; \
    mode_t mode=0; if(has_mode(flags)){va_list ap;va_start(ap,flags);mode=va_arg(ap,mode_t);va_end(ap);} \
    int (*fn)(const char*,int,...)=dlsym(RTLD_NEXT,#name);return fn(path,flags,mode); \
}
#define OPENAT_WRAPPER(name) \
int name(int dir,const char *path,int flags,...) { \
    if(denied(path))return -1; \
    mode_t mode=0; if(has_mode(flags)){va_list ap;va_start(ap,flags);mode=va_arg(ap,mode_t);va_end(ap);} \
    int (*fn)(int,const char*,int,...)=dlsym(RTLD_NEXT,#name);return fn(dir,path,flags,mode); \
}
OPEN_WRAPPER(open)
OPEN_WRAPPER(open64)
OPENAT_WRAPPER(openat)
OPENAT_WRAPPER(openat64)
int __open_2(const char *p,int f) {return open(p,f);}
int __open64_2(const char *p,int f) {return open64(p,f);}
int __openat_2(int d,const char *p,int f) {return openat(d,p,f);}
int __openat64_2(int d,const char *p,int f) {return openat64(d,p,f);}
