const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../armbian/sensor-relay/codertools-motion-fix.js'),'utf8');
function setup(host='www.codertools.net'){
 const cube={style:{transform:'',setProperty(k,v){this[k]=v}}},callbacks=[];
 const sandbox={location:{hostname:host,pathname:'/tools/motion-sensor-test.php'},document:{getElementById:()=>cube},MutationObserver:class{constructor(f){callbacks.push(f)}observe(){}disconnect(){}}};
 vm.runInNewContext(code,sandbox);return {cube,render(a,b,g){cube.style.transform=`rotateX(${-b}deg) rotateY(${g}deg) rotateZ(${a}deg)`;for(const c of callbacks)c();return cube.style.transform;}};
}
function mul(a,b){const [w,x,y,z]=a,[v,i,j,k]=b;return [w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v]}
function axis(i,d){const t=d*Math.PI/360,v=[0,0,0];v[i]=Math.sin(t);return [Math.cos(t),...v]}
function rot(q,v){return mul(mul(q,[0,...v]),[q[0],-q[1],-q[2],-q[3]]).slice(1)}
const f=setup();assert.equal(f.cube.style.transition,'none');
for(const [a,b,g] of [[0,0,0],[30,0,0],[0,30,0],[0,0,30],[359,25,-40],[1,25,-40],[120,90,0],[80,140,70]]){
 const s=f.render(a,b,g);assert.ok(s.startsWith('matrix3d('));const m=s.slice(9,-1).split(',').map(Number),q=mul(mul(axis(2,a),axis(0,b)),axis(1,g));
 for(let i=0;i<3;i++){const css=[0,0,0];css[i]=1;const w3c=[css[0],-css[1],css[2]],r=rot(q,w3c),expected=[r[0],-r[1],r[2]];for(let j=0;j<3;j++)assert.ok(Math.abs(m[4*i+j]-expected[j])<1e-10)}
}
const outside=setup('example.com');assert.ok(outside.render(1,2,3).startsWith('rotateX('));
console.log('PASS: CSS matrix matches quaternion rotation for all axes, alpha wrap, beta90/140; transition disabled; unrelated host untouched');
