/* Read-only per-process metadata tap; never changes mapped parameters. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <unistd.h>
static struct {void *address;size_t length;off_t offset;} maps[16];
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER;
void *mmap(void *a,size_t n,int prot,int flags,int fd,off_t off) {
    void *(*real_mmap)(void*,size_t,int,int,int,off_t)=dlsym(RTLD_NEXT,"mmap");
    void *result=real_mmap(a,n,prot,flags,fd,off);
    char link[64],name[128];snprintf(link,sizeof(link),"/proc/self/fd/%d",fd);
    ssize_t count=readlink(link,name,sizeof(name)-1);
    if(count>=0)name[count]=0;
    if(result!=MAP_FAILED && count>=0 && !strcmp(name,"/dev/video30") && n>=10825) {
        pthread_mutex_lock(&lock);
        for(int i=0;i<16;i++)if(!maps[i].address){maps[i].address=result;maps[i].length=n;maps[i].offset=off;break;}
        pthread_mutex_unlock(&lock);
    }
    return result;
}
void *mmap64(void *a,size_t n,int prot,int flags,int fd,off64_t off) {
    return mmap(a,n,prot,flags,fd,(off_t)off);
}
int munmap(void *address,size_t length) {
    int (*real_munmap)(void*,size_t)=dlsym(RTLD_NEXT,"munmap");
    pthread_mutex_lock(&lock);
    for(int i=0;i<16;i++)if(maps[i].address==address)maps[i].address=NULL;
    pthread_mutex_unlock(&lock);
    return real_munmap(address,length);
}
int f8_dump_params(void) {
    int saved=0;pthread_mutex_lock(&lock);
    for(int i=0;i<16;i++)if(maps[i].address) {
        char path[160];snprintf(path,sizeof(path),"/run/f8-camera-c4/params-tap-%d.bin",i);
        int fd=open(path,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0644);
        if(fd>=0){ssize_t n=write(fd,maps[i].address,maps[i].length);close(fd);if(n==(ssize_t)maps[i].length)saved++;}
    }
    pthread_mutex_unlock(&lock);return saved;
}
