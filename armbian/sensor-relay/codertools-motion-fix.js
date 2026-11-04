/* CoderTools motion cube: render W3C Z-X-Y orientation as one CSS matrix.
   Site-local presentation fix; no sensor/API values or permissions are changed. */
(()=>{
 'use strict';
 if(!['www.codertools.net','codertools.net'].includes(location.hostname)||location.pathname!=='/tools/motion-sensor-test.php')return;
 if(globalThis.__f8MotionCubeMatrixFix)return;globalThis.__f8MotionCubeMatrixFix=true;
 const pattern=/^rotateX\(([-+\d.eE]+)deg\)\s*rotateY\(([-+\d.eE]+)deg\)\s*rotateZ\(([-+\d.eE]+)deg\)$/;
 function repair(cube){
  const m=cube.style.transform.match(pattern);if(!m)return;
  const a=Number(m[3])*Math.PI/180,b=-Number(m[1])*Math.PI/180,g=Number(m[2])*Math.PI/180;
  if(![a,b,g].every(Number.isFinite))return;
  const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b),cg=Math.cos(g),sg=Math.sin(g);
  const r00=ca*cg-sa*sb*sg,r01=-sa*cb,r02=ca*sg+sa*sb*cg;
  const r10=sa*cg+ca*sb*sg,r11=ca*cb,r12=sa*sg-ca*sb*cg;
  const r20=-cb*sg,r21=sb,r22=cb*cg;
  // W3C screen axes to CSS coordinates: S*R*S, S=diag(1,-1,1).
  const matrix=[r00,-r10,r20,0,-r01,r11,-r21,0,r02,-r12,r22,0,0,0,0,1];
  cube.style.transform='matrix3d('+matrix.map(v=>Math.abs(v)<1e-12?0:v).join(',')+')';
 }
 function attach(){
  const cube=document.getElementById('cube3d');if(!cube)return false;
  cube.style.setProperty('transition','none','important');
  const observer=new MutationObserver(()=>repair(cube));observer.observe(cube,{attributes:true,attributeFilter:['style']});repair(cube);return true;
 }
 if(!attach()){
  const finder=new MutationObserver(()=>{if(attach())finder.disconnect();});finder.observe(document,{childList:true,subtree:true});
 }
})();
