const {chromium}=require('playwright');
(async()=>{
  const [,,html,out,mode]=process.argv;
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  await p.goto('file://'+html);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(500);
  const times=mode==='preview'?[0.6,1.2,3,4.2,5.6,7.3,8.2,9.2,10.5,11.5,14.2]:Array.from({length:450},(_,i)=>i/30);
  for(let i=0;i<times.length;i++){await p.evaluate(([t,f])=>window.render(t,f),[times[i],i]);
    await p.screenshot({path:`${out}/${mode==='preview'?'p_'+times[i]:'f'+String(i).padStart(4,'0')}.${mode==='preview'?'png':'jpg'}`,type:mode==='preview'?'png':'jpeg',...(mode==='preview'?{}:{quality:93})});}
  await b.close();})();
