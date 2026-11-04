/* Ignore incomplete OV8858 OTP metadata in this camera process only.
 * Never writes sensor OTP, kernel memory, or replacement calibration values.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <linux/videodev2.h>
#include <linux/rk-camera-module.h>
_Static_assert(sizeof(struct rkmodule_inf)==5207,"RKMODULE ABI changed");
int ioctl(int fd,unsigned long request,...) {
    int (*real_ioctl)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");
    va_list ap;va_start(ap,request);void *arg=va_arg(ap,void *);va_end(ap);
    int result=real_ioctl(fd,request,arg);
    if(result || request!=RKMODULE_GET_MODULE_INFO || !arg)return result;
    struct rkmodule_inf *info=arg;
    if(strncmp(info->base.sensor,"ov8858",sizeof(info->base.sensor)) ||
       strncmp(info->base.module,"HS5885-BNSM1018-V01",sizeof(info->base.module)))return result;
    if(info->awb.flag && (!info->awb.r_value || !info->awb.b_value ||
       !info->awb.gr_value || !info->awb.gb_value || !info->awb.golden_r_value ||
       !info->awb.golden_b_value || !info->awb.golden_gr_value || !info->awb.golden_gb_value)) {
        info->awb.flag=0;
        fprintf(stderr,"F8 AIQ OV8858: ignoring incomplete AWB OTP, using IQ calibration\n");
    }
    if(info->lsc.flag && (!info->lsc.width || !info->lsc.height ||
       !info->lsc.table_size || info->lsc.table_size>RKMODULE_LSCDATA_LEN)) {
        info->lsc.flag=0;
        fprintf(stderr,"F8 AIQ OV8858: ignoring incomplete LSC OTP, using IQ calibration\n");
    }
    return result;
}
