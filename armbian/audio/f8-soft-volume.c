/* F8 speaker curve: sqrt(native amplitude), unity at maximum. */
#include "ladspa.h"
#include <math.h>
#include <stdlib.h>
typedef struct { LADSPA_Data *in,*out,*volume; float current; } State;
static LADSPA_Handle make(const LADSPA_Descriptor *d,unsigned long rate){(void)d;(void)rate;return calloc(1,sizeof(State));}
static void connect_port(LADSPA_Handle h,unsigned long p,LADSPA_Data *v){State*s=h;if(p==0)s->in=v;else if(p==1)s->out=v;else if(p==2)s->volume=v;}
static void activate(LADSPA_Handle h){((State*)h)->current=0;}
static void run(LADSPA_Handle h,unsigned long n){State*s=h;float v=*s->volume; if(!isfinite(v))v=0;v=fminf(1,fmaxf(0,v));float goal=sqrtf(v);for(unsigned long i=0;i<n;i++){s->current+=fminf(1.0f/240,fmaxf(-1.0f/240,goal-s->current));s->out[i]=s->in[i]*s->current;}}
static void cleanup(LADSPA_Handle h){free(h);}
static const LADSPA_PortDescriptor ports[]={LADSPA_PORT_INPUT|LADSPA_PORT_AUDIO,LADSPA_PORT_OUTPUT|LADSPA_PORT_AUDIO,LADSPA_PORT_INPUT|LADSPA_PORT_CONTROL};
static const char *const names[]={"In","Out","Volume"};
static const LADSPA_PortRangeHint hints[]={{0,0,0},{0,0,0},{LADSPA_HINT_BOUNDED_BELOW|LADSPA_HINT_BOUNDED_ABOVE|LADSPA_HINT_DEFAULT_0,0,1}};
static const LADSPA_Descriptor descriptor={.UniqueID=0xF835,.Label="f8_soft_volume",.Properties=LADSPA_PROPERTY_HARD_RT_CAPABLE,.Name="F8 Soft Speaker Volume",.Maker="F8 port",.Copyright="MIT",.PortCount=3,.PortDescriptors=ports,.PortNames=names,.PortRangeHints=hints,.instantiate=make,.connect_port=connect_port,.activate=activate,.run=run,.cleanup=cleanup};
const LADSPA_Descriptor *ladspa_descriptor(unsigned long index){return index==0?&descriptor:NULL;}
