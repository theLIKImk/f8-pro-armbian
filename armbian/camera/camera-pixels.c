/* Full-range BT.601 NV12 -> RGB preview conversion. No ISP/calibration edits. */
#include <stddef.h>
#include <stdint.h>
static unsigned char clip(int value) {return value<0?0:value>255?255:(unsigned char)value;}
int f8_nv12_rgb(const unsigned char *src,size_t src_size,unsigned char *rgb,
                size_t rgb_size,unsigned int width,unsigned int height) {
    if(!src || !rgb || !width || !height || width>4096 || height>4096 || (width&1) || (height&1))return -1;
    size_t pixels=(size_t)width*height;
    if(src_size<pixels*3/2 || rgb_size<pixels*3)return -2;
    const unsigned char *uv=src+pixels;
    for(unsigned int row=0;row<height;row++)for(unsigned int col=0;col<width;col++) {
        size_t pixel=(size_t)row*width+col;
        size_t chroma=(size_t)(row/2)*width+(col&~1U);
        int y=src[pixel],u=(int)uv[chroma]-128,v=(int)uv[chroma+1]-128;
        rgb[pixel*3]=clip(y+((359*v+128)>>8));
        rgb[pixel*3+1]=clip(y-((88*u+183*v+128)>>8));
        rgb[pixel*3+2]=clip(y+((454*u+128)>>8));
    }
    return 0;
}
