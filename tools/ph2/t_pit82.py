import sys,json
from playwright.sync_api import sync_playwright
f=sys.argv[1];s0=float(sys.argv[2]);bx=int(sys.argv[3]) if len(sys.argv)>3 else -1
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':640,'height':400});E=[];pg.on('pageerror',lambda e:E.append(str(e)[:300]));ev=pg.evaluate
    pg.goto('http://127.0.0.1:8123/'+f);pg.wait_for_function("()=>{try{return state=='ready'&&typeof loop=='function'}catch(e){return false}}",timeout=60000);pg.wait_for_timeout(1000)
    ev("()=>{window.__ft=0;window.requestAnimationFrame=fn=>{setTimeout(()=>{__ft+=1000/60;fn(__ft)},0)}}")
    ev("()=>{cfg.trk=7;cfg.riv=0;cfg.laps=5;cfg.grid='r';cfg.sc=0;cfg.wx=0;start();cd=.01}");pg.wait_for_timeout(1500)
    ev("""([s0,bx])=>{R.render=()=>{};window.__l=[];window.__mx={hit:0,stop:null};
    TESTU=c=>{const o=ai(c);return{st:Math.max(-1,Math.min(1,-(2*Math.sin(o.df)/Math.max(6,o.dd))/Math.min(.14,.9*DYP.mu*(c.G||1)*(9.81+DYP.dn*c.s*c.s/DYP.m)/Math.max(c.s*c.s,60)))),th:o.th,br:o.br}};
    const c=cars[0];let j=0,bb=1e9;for(let i=0;i<N;i++){const d=Math.abs(sOf(i)-s0);if(d<bb){bb=d;j=i}}const q=P[j];c.x=q.x;c.z=q.z;c.h=Math.atan2(T[j].x,T[j].z);c.vx=T[j].x*45;c.vz=T[j].z*45;c.s=45;c.idx=j;c.lane=0;c.d=0;c.lap=1;c.pitReq=1;c.nxt='H';if(bx>=0)c.box=bx;
    let k=0;setInterval(()=>{const x=cars[0];const s=sOf(x.idx);__mx.hit=Math.max(__mx.hit,x.hit||0);
      if(x.s<1&&x.pitT>0&&!__mx.stop)__mx.stop={s:+s.toFixed(1),d:+x.d.toFixed(2),box:x.box,boxS:+boxS(x).toFixed(1),B:PIT.B};
      if(k++%8==0)__l.push([+s.toFixed(0),+x.d.toFixed(1),(x.s*3.6)|0,x.pl?1:0,+(x.hit||0).toFixed(1),+(x.pitT||0).toFixed(1),x.svc?1:0,x.pits])},25)}""",[s0,bx])
    for i in range(60):
        pg.wait_for_timeout(1500)
        r=ev("()=>{const x=cars[0];return [sOf(x.idx)|0,x.pits,x.pl,x.lap,x.dnf]}")
        if r[1]>=1 and r[0]>PITX_END if False else (r[1]>=1 and r[0]>250):break
    L=ev("()=>__l");mx=ev("()=>__mx");print('final',r,'errors',E,'maxhit',mx['hit'],'stop',mx['stop'])
    maxsp=max([q[2] for q in L if q[3]]+[0]);print('max speed while pl(km/h)',maxsp,'samples',len(L))
    for q in L[::2][:80]:print(q)
    b.close()
