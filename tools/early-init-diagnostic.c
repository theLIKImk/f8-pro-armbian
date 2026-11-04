/* F8-PRO diagnostic-only PID1 handoff and framebuffer status monitor.
 * No network credentials, shell, driver changes or GPU libraries required.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <ifaddrs.h>
#include <linux/fb.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/* Original small 5x7 uppercase glyphs, rows encoded in five low bits. */
static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-/: ";
static const unsigned char glyph[][7] = {
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},
 {30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
 {14,17,16,23,17,17,14},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},
 {7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
 {17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},
 {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
 {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
 {17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
 {17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
 {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
 {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},
 {14,17,17,15,1,1,14},{0,0,0,0,0,6,6},{0,0,0,31,0,0,0},
 {1,2,2,4,8,8,16},{0,4,4,0,4,4,0},{0,0,0,0,0,0,0}
};
static int fb = -1;
static unsigned char *pixels;
static struct fb_fix_screeninfo fix;
static struct fb_var_screeninfo var;

static int open_fb(void) {
    if (fb >= 0) return 1;
    fb = open("/dev/fb0", O_RDWR | O_CLOEXEC);
    if (fb < 0) return 0;
    if (ioctl(fb, FBIOGET_FSCREENINFO, &fix) || ioctl(fb, FBIOGET_VSCREENINFO, &var)) goto fail;
    if (fix.type != FB_TYPE_PACKED_PIXELS || fix.visual != FB_VISUAL_TRUECOLOR ||
        (var.bits_per_pixel != 16 && var.bits_per_pixel != 32) ||
        !fix.smem_len || fix.smem_len > 256U*1024*1024 ||
        !var.xres || !var.yres || var.xres > 8192 || var.yres > 8192 ||
        var.red.length > 8 || var.green.length > 8 || var.blue.length > 8 ||
        var.transp.length > 8 || var.red.offset + var.red.length > var.bits_per_pixel ||
        var.green.offset + var.green.length > var.bits_per_pixel ||
        var.blue.offset + var.blue.length > var.bits_per_pixel ||
        var.transp.offset + var.transp.length > var.bits_per_pixel ||
        ((uint64_t)var.xoffset + var.xres) * (var.bits_per_pixel/8) > fix.line_length ||
        ((uint64_t)var.yoffset + var.yres) * fix.line_length > fix.smem_len) goto fail;
    pixels = mmap(NULL, fix.smem_len, PROT_READ|PROT_WRITE, MAP_SHARED, fb, 0);
    if (pixels == MAP_FAILED) goto fail;
    return 1;
fail:
    close(fb); fb=-1; return 0;
}
static uint32_t channel(unsigned c, struct fb_bitfield f) {
    return f.length ? ((c >> (8-f.length)) << f.offset) : 0;
}
static uint32_t color(unsigned r, unsigned g, unsigned b) {
    return channel(r,var.red)|channel(g,var.green)|channel(b,var.blue)|channel(255,var.transp);
}
static void pixel(unsigned x,unsigned y,uint32_t c) {
    if (x>=var.xres || y>=var.yres) return;
    size_t off=((size_t)y+var.yoffset)*fix.line_length+((size_t)x+var.xoffset)*(var.bits_per_pixel/8);
    if (var.bits_per_pixel==32) memcpy(pixels+off,&c,4);
    else { uint16_t v=(uint16_t)c; memcpy(pixels+off,&v,2); }
}
static void line(unsigned n,const char *text,uint32_t ink) {
    unsigned scale=var.xres>=800 ? 4 : 2, top=20+n*9*scale;
    for (unsigned y=top;y<top+8*scale && y<var.yres;y++)
        for(unsigned x=0;x<var.xres;x++) pixel(x,y,color(0,0,0));
    for(unsigned i=0;text[i] && 20+(i+1)*6*scale<var.xres;i++) {
        const char *p=strchr(alphabet,text[i]);
        if(!p) continue;
        for(unsigned y=0;y<7;y++) for(unsigned x=0;x<5;x++)
            if(glyph[p-alphabet][y] & (1U<<(4-x)))
                for(unsigned dy=0;dy<scale;dy++) for(unsigned dx=0;dx<scale;dx++)
                    pixel(20+i*6*scale+x*scale+dx,top+y*scale+dy,ink);
    }
}
static void ipv4(char *dest,size_t length) {
    struct ifaddrs *list=NULL;
    snprintf(dest,length,"IP WAIT");
    if(getifaddrs(&list)) return;
    for(struct ifaddrs *p=list;p;p=p->ifa_next) {
        if(!p->ifa_addr || p->ifa_addr->sa_family!=AF_INET || !strcmp(p->ifa_name,"lo")) continue;
        struct sockaddr_in *addr=(struct sockaddr_in*)p->ifa_addr;
        uint32_t a=ntohl(addr->sin_addr.s_addr);
        if(!a || (a>>24)==127 || (a>>16)==0xa9fe) continue;
        char value[INET_ADDRSTRLEN];
        if(inet_ntop(AF_INET,&addr->sin_addr,value,sizeof(value))) snprintf(dest,length,"IP %s",value);
        break;
    }
    freeifaddrs(list);
}
static void monitor(int exec_error) {
    for(unsigned t=0;t<600;t++) {
        if(open_fb()) {
            char status[80],ip[80],comm[32]="";
            FILE *f=fopen("/proc/1/comm","r");
            if(f) { if(!fgets(comm,sizeof(comm),f)) comm[0]=0; fclose(f); }
            unsigned good=color(80,240,130),white=color(240,240,240);
            line(0,"F8 PRO DIAGNOSTIC",white);
            line(1,"ROOTFS INIT REACHED",good);
            if(exec_error) { snprintf(status,sizeof(status),"SYSTEMD EXEC ERROR %d",exec_error); line(2,status,color(255,80,80)); }
            else line(2,!strncmp(comm,"systemd",7)?"PID1 SYSTEMD":"SYSTEMD HANDOFF WAIT",white);
            line(3,access("/run/dbus/system_bus_socket",F_OK)==0?"DBUS SOCKET PRESENT":"DBUS WAIT",white);
            line(4,access("/run/NetworkManager/NetworkManager.pid",F_OK)==0?"NM PID FILE PRESENT":"NM PID FILE WAIT",white);
            line(5,access("/run/sshd.pid",F_OK)==0?"SSH PID FILE PRESENT":"SSH PID FILE WAIT",white);
            ipv4(ip,sizeof(ip)); line(6,ip,white);
            snprintf(status,sizeof(status),"MONITOR %u SECONDS",t*2); line(7,status,white);
            line(8,"STATUS FILES ARE NOT HEALTH CHECKS",white);
        }
        sleep(2);
    }
}
int main(int argc,char **argv) {
    if(argc==2 && (!strcmp(argv[1],"--usb-log-monitor") || !strcmp(argv[1],"--arch-log-monitor"))) {
        int handoff=!strcmp(argv[1],"--arch-log-monitor");
        for(unsigned t=0;t<600;t++) {
            if(open_fb()) {
                char phase[96]="USB LOG PREPARING";
                FILE *f=fopen("/run/f8-phase","r");
                if(f) { if(!fgets(phase,sizeof(phase),f)) phase[0]=0; fclose(f); }
                phase[strcspn(phase,"\r\n")]=0;
                for(char *p=phase;*p;p++) if(!strchr(alphabet,*p)) *p=' ';
                line(0,"F8 PRO USB LOG",color(240,240,240));
                line(1,handoff?"ARCH INIT HANDOFF":"RAMDISK INIT REACHED",color(80,240,130));
                line(2,phase,color(240,240,240));
                line(3,handoff?"ROOTFS NORMAL BOOT":"ROOTFS IS READ ONLY",color(240,240,240));
                line(4,"CHECK USB DRIVE ON COMPUTER",color(240,240,240));
            }
            sleep(2);
        }
        return 0;
    }
    if(argc==2 && !strcmp(argv[1],"--self-test")) {
        if(sizeof(glyph)/sizeof(glyph[0])!=strlen(alphabet)) return 1;
        for(size_t i=0;i<sizeof(glyph);i++) if(((unsigned char*)glyph)[i]>31) return 1;
        puts("PASS: static diagnostic starts; font bounds valid"); return 0;
    }
    if(getpid()!=1) { execv("/usr/lib/systemd/systemd",argv); perror("systemd"); return 1; }
    /* Give the built-in display driver up to ten seconds to expose fb0. */
    for(unsigned i=0;i<100;i++) { if(open_fb()) break; usleep(100000); }
    if(fb>=0) {
        line(0,"F8 PRO DIAGNOSTIC",color(240,240,240));
        line(1,"ROOTFS INIT REACHED",color(80,240,130));
        line(2,"SYSTEMD HANDOFF",color(240,240,240));
    }
    pid_t child=fork();
    if(child==0) { monitor(0); _exit(0); }
    execv("/usr/lib/systemd/systemd",argv);
    int saved=errno;
    if(child>0) kill(child,15);
    for(;;) monitor(saved);
}
