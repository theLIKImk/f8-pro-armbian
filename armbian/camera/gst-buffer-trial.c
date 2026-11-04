/* Diagnostic only: request four MMAP buffers on the proven rear ISP output.
 * Does not change formats, queue operations, returned frames or driver state.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <linux/videodev2.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
static int (*real_ioctl)(int,unsigned long,...);
__attribute__((constructor)) static void init(void) { real_ioctl=dlsym(RTLD_NEXT,"ioctl"); }
int ioctl(int fd,unsigned long request,...) {
    va_list ap;va_start(ap,request);void *arg=va_arg(ap,void*);va_end(ap);
    if(request==VIDIOC_REQBUFS && arg) {
        struct v4l2_requestbuffers *r=arg;
        if(r->type==V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE && r->memory==V4L2_MEMORY_MMAP && r->count>0 && r->count<4) {
            struct v4l2_capability c={0};
            if(real_ioctl(fd,VIDIOC_QUERYCAP,&c)==0 && !strcmp((char*)c.driver,"rkisp_v6") && !strcmp((char*)c.card,"rkisp_mainpath") && !strcmp((char*)c.bus_info,"platform:rkisp0-vir0")) {
                fprintf(stderr,"F8 GST diagnostic: request %u -> 4 rear MMAP buffers\n",r->count);r->count=4;
            }
        }
    }
    return real_ioctl(fd,request,arg);
}
