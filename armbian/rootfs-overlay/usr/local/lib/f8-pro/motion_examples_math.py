"""Relative gyro pose only; no invented absolute attitude or compass fusion."""
import math

def norm(v):return math.sqrt(sum(x*x for x in v))
def multiply(a,b):
 w,x,y,z=a;v,i,j,k=b
 return (w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v)
def rotate(q,v):return multiply(multiply(q,(0,*v)),(q[0],-q[1],-q[2],-q[3]))[1:]
def mapped(matrix,v):return [sum(a*b for a,b in zip(row,v)) for row in matrix]

class GyroPose:
 def __init__(self):
  self.q=(1.,0.,0.,0.);self.bias=[0.,0.,0.];self.last=None;self.samples=None;self.started=None;self.message='轻缓转动平板，观察正方体；可静置校零。';self.gaps=0
 def reset(self):
  self.q=(1.,0.,0.,0.);self.last=None;self.samples=None;self.message='相对姿态已归零；保留本次会话的零偏。'
 def calibrate(self):
  self.samples=[];self.started=None;self.message='请保持平板静止约2秒…'
 def advance(self,rate,stamp,accel=None):
  if rate is None or len(rate)!=3 or not all(math.isfinite(x) for x in rate):self.last=None;return
  dt=0 if self.last is None else stamp-self.last;self.last=stamp
  if dt<0 or dt>.25:
   self.gaps+=1;dt=0
   if self.samples is not None:self.samples=None;self.message='采样中断，静置后重试校零。'
  if self.samples is not None:
   if self.started is None:self.started=stamp
   if accel is not None:self.samples.append((list(rate),list(accel)))
   elapsed=stamp-self.started
   if elapsed>=1.5 and len(self.samples)>=20:
    n=len(self.samples);means=[[sum(s[k][i] for s in self.samples)/n for i in range(3)] for k in [0,1]]
    spread=[math.sqrt(sum(sum((s[k][i]-means[k][i])**2 for i in range(3)) for s in self.samples)/n) for k in [0,1]]
    if spread[0]>.02 or spread[1]>.25 or norm(means[0])>.08 or not 9<norm(means[1])<10.7:self.message='检测到移动或读数异常，保持静止后重试。'
    else:self.bias=means[0];self.q=(1.,0.,0.,0.);self.message='静置校零完成（仅本次会话）；正方体已归零。'
    self.samples=None;return
   if elapsed>5:self.samples=None;self.message='有效采样不足，请恢复读取后重试。'
  omega=[rate[i]-self.bias[i] for i in range(3)];speed=norm(omega);angle=speed*dt
  if speed>1e-10 and dt>0:
   delta=(math.cos(angle/2),*(v/speed*math.sin(angle/2) for v in omega));q=multiply(self.q,delta);length=norm(q);self.q=tuple(v/length for v in q)
