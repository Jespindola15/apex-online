import sys,json
from playwright.sync_api import sync_playwright
f=sys.argv[1];laps=float(sys.argv[2])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':640,'height':400});E=[];pg.on('pageerror',lambda e:E.append(str(e)[:300]));ev=pg.evaluate
    pg.goto('http://127.0.0.1:8123/'+f);pg.wait_for_function("()=>{try{return state=='ready'&&typeof loop=='function'}catch(e){return false}}",timeout=60000);pg.wait_for_timeout(1500)
    ev("()=>{window.__ft=0;window.requestAnimationFrame=fn=>{setTimeout(()=>{__ft+=1000/60;fn(__ft)},0)}}")
    ev("()=>{cfg.trk=7;cfg.riv=19;cfg.laps=9;cfg.mode='q';cfg.grid='r';cfg.sc=0;cfg.wx=0;start();cd=.01}");pg.wait_for_timeout(1500)
    ev("""()=>{R.render=()=>{};window.__st={};window.__mxs={};window.__hit={};window.__sp=[];
    TESTU=c=>{const o=ai(c);return{st:Math.max(-1,Math.min(1,-(2*Math.sin(o.df)/Math.max(6,o.dd))/Math.min(.14,.9*DYP.mu*(c.G||1)*(9.81+DYP.dn*c.s*c.s/DYP.m)/Math.max(c.s*c.s,60)))),th:o.th,br:o.br}};
    window.__iv=setInterval(()=>{if(state!='race')return;const tt=t;cars.forEach((c,i)=>{if(c.dnf||c.gone)return;const s=sOf(c.idx);
      if(c.pitT>0&&c.s<1)__st[i+':'+c.pits]=[+s.toFixed(1),+c.d.toFixed(2),c.box,c.pl?1:0];
      if(c.pl&&s>PIT.sLane&&s<PIT.sEnd)__mxs[i]=Math.max(__mxs[i]||0,c.s*3.6);
      if((c.hit||0)>.8&&s>PIT.sEnt&&s<PIT.sExit)__hit[i]=(__hit[i]||0)+1;
    });
    if(tt>25&&!window.__pt){window.__pt=1;cars.forEach((c,i)=>{c.pitReq=1;c.nxt=pickNext(c)})}},50)}""")
    for i in range(400):
        pg.wait_for_timeout(1500)
        r=ev("()=>[t|0,Math.max(...cars.map(c=>c.lap)),cars.filter(c=>c.pits).length]")
        if r[1]>=laps+1 or r[2]>=19 and r[0]>200:break
    res=ev("()=>({st:__st,mx:__mxs,hit:__hit,pits:cars.filter(c=>c.pits).length,dnf:cars.filter(c=>c.dnf).map(c=>[c.idx,sOf(c.idx)|0]),bs:Array.from({length:PIT.nb},(_,k)=>+PIT.bs(k).toFixed(1)),nb:PIT.nb,t:t|0})")
    print('t',res['t'],'pits',res['pits'],'dnf',res['dnf'],'errors',E,'hit-in-pit',res['hit'])
    bs=res['bs'];errs=[]
    for k,v in sorted(res['st'].items(),key=lambda x:x[1][0]):
        n=min(bs,key=lambda x:abs(x-v[0]));errs.append(abs(n-v[0]));print(k,v,'nearest box s',n,'err',round(abs(n-v[0]),1))
    print('stops',len(errs),'max err s',max(errs) if errs else None,'speed in lane max km/h',max(res['mx'].values()) if res['mx'] else None)
    b.close()
