// SPDX-License-Identifier: GPL-2.0
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>
static void wait_ms(int ms){struct timespec t={ms/1000,(ms%1000)*1000000L};while(nanosleep(&t,&t)<0&&errno==EINTR){}}
static int motor(void){int v=-1;FILE *f=fopen("/sys/devices/platform/f8-cover-haptic/motor_active","r");if(f){if(fscanf(f,"%d",&v)!=1)v=-1;fclose(f);}return v;}
int main(int argc,char **argv){
 int ms=80,count=1,test=0;
 for(int i=1;i<argc;i++){
  if(!strcmp(argv[i],"--milliseconds")&&i+1<argc)ms=atoi(argv[++i]);
  else if(!strcmp(argv[i],"--count")&&i+1<argc)count=atoi(argv[++i]);
  else if(!strcmp(argv[i],"--watchdog-test"))test=1;
  else return 2;
 }
 if(ms<1||ms>200||count<1||count>3)return 2;
 int fd=open("/dev/input/f8-haptic",O_RDWR|O_CLOEXEC);if(fd<0){perror("haptic open");return 1;}
 char name[128]={0};if(ioctl(fd,EVIOCGNAME(sizeof(name)),name)<0||strcmp(name,"F8 Haptic Motor")){close(fd);return 1;}
 if(motor()!=0){fprintf(stderr,"Motor busy; preserve existing effect\n");close(fd);return 1;}
 struct ff_effect effect={0};effect.type=FF_RUMBLE;effect.id=-1;effect.u.rumble.strong_magnitude=0x8000;effect.replay.length=test?1000:ms;
 if(ioctl(fd,EVIOCSFF,&effect)<0){perror("effect upload");close(fd);return 1;}
 int seen=0,off=0;
 for(int n=0;n<(test?1:count);n++){
  struct input_event e={0};e.type=EV_FF;e.code=effect.id;e.value=1;
  if(write(fd,&e,sizeof(e))!=sizeof(e)){perror("effect play");close(fd);return 1;}
  wait_ms(20);if(motor()==1)seen++;
  wait_ms((test?300:ms+80)-20);if(motor()==0)off++;
  e.value=0;if(write(fd,&e,sizeof(e))!=sizeof(e)){close(fd);return 1;}wait_ms(250);
 }
 ioctl(fd,EVIOCRMFF,effect.id);close(fd);wait_ms(30);
 printf("{\"pulses\":%d,\"requested_ms\":%d,\"observed_on\":%d,\"observed_off\":%d,\"motor_after_close\":%d,\"watchdog_test\":%s}\n",test?1:count,test?1000:ms,seen,off,motor(),test?"true":"false");
 return seen==(test?1:count)&&off==(test?1:count)&&motor()==0?0:1;
}
