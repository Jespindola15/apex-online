import numpy as np,json,re
s=open('menu/index.v81.html',encoding='utf8').read()
e=json.load(open('monza/entry.json'));P=np.array(e['pts']);W=np.array(e['wd'])
c=np.load('monza/centre_game.npy')
i0=np.argmin(np.hypot(*(c-P[0]).T))
if np.dot(c[(i0+5)%len(c)]-c[i0],P[5]-P[0])<0: c=c[::-1];i0=np.argmin(np.hypot(*(c-P[0]).T))
c=np.roll(c,-i0,axis=0)
d=np.r_[0,np.cumsum(np.hypot(*np.diff(np.r_[c,c[:1]],axis=0).T))];tot=d[-1]
S0=316.0
t=S0+np.linspace(0,tot,721,endpoint=False);t=np.mod(t,tot)
cc=np.r_[c,c[:1]]
Q=np.c_[np.interp(t,d,cc[:,0]),np.interp(t,d,cc[:,1])]
idx=np.array([np.argmin(np.hypot(*(P-q).T)) for q in Q]);W2=W[idx]
fmt=lambda a:'['+','.join('[%.1f,%.1f]'%(x,y) for x,y in a)+']'
j=s.find("n:'Monza (Assetto Corsa)'");k=s.find("pts:[[",j);k2=s.find("]],",k)+2
w0=s.find("wd:[",k2);w1=s.find("]",w0)
f0=S0/tot;Nn=2517;shN=int(round(S0/2.3))
a0,a1=(2002-shN)%Nn,(2211-shN)%Nn
frac=lambda x:round((x-f0)%1,4)
drs="drs:[[%s,%s,%s],[%s,%s,%s]]"%(frac(.88),frac(.029),frac(.152),frac(.482),frac(.529),frac(.674))
S=json.load(open('ph2/nodes_sl.json'))
gs=[[round(S['AC_START_%d'%i][0]-S0,1),round(S['AC_START_%d'%i][1],1)] for i in range(26)]
pb=[S['AC_PIT_%d'%i] for i in range(26)]
bs=sorted(round(p[0]-S0,1) for p in pb);Bm=float(np.mean([p[1] for p in pb]))
q=np.load('ph2/pitlane_sl.npy');ps,pl=q[:,0],q[:,1]
SE,SL,SN,SX=-290.,-110.,300.,520.
f=[]
for x in np.arange(SE,SX+.1,10.):
    f+= [round(x-S0,1),round(float(max(.3,np.interp(x,ps,pl))),1)]
F=round(float(np.median(pl[(ps>SL)&(ps<SN)])),1)
pit={"sg":1,"sEnt":SE-S0,"sLane":SL-S0,"sEnd":SN-S0,"sExit":SX-S0,"F":F,"B":round(Bm,1),"G":round(Bm+4,1),"bs":bs,"f":f}
print('F',F,'B',Bm,'bs',bs[:3],bs[-1],'gs',gs[:3],gs[-1],'drs',drs,'aif',a0,a1)
head=s[j:k].replace("k:1,aif:[[2002,2211,.84]]","k:1,aif:[[%d,%d,.84]],gs:%s,pit:%s"%(a0,a1,json.dumps(gs,separators=(',',':')),json.dumps(pit,separators=(',',':')))).replace("drs:[[.88,.029,.152],[.482,.529,.674]]",drs)
assert 'gs:' in head and 'pit:' in head and 'drs:[['+str(frac(.88)) in head
new=s[:j]+head+"pts:"+fmt(Q)+s[k2:w0]+"wd:["+','.join('%.1f'%x for x in np.roll(W2,0))+s[w1:]
# W2 already index-mapped to shifted Q
def rep(old,nw,cnt=1):
    global new
    assert new.count(old)==cnt,(old[:40],new.count(old))
    new=new.replace(old,nw)
rep("k=N-6-slot*(nn>12?5:7),n=Nm[k],lane=GLN(k,slot%2?-3.2:3.2);","GS=TRACKS[trkIdx].gs,GU=GS&&slot<GS.length,k=GU?((Math.round(GS[slot][0]*N/TLEN)%N+N)%N):N-6-slot*(nn>12?5:7),n=Nm[k],lane=GU?GS[slot][1]:GLN(k,slot%2?-3.2:3.2);")
rep("const k=((N-6-sl*(nn>12?5:7))%N+N)%N,ln=sl%2?-3.2:3.2,","const GS=TRACKS[trkIdx].gs,GU=GS&&sl<GS.length,k=GU?((Math.round(GS[sl][0]*N/TLEN)%N+N)%N):((N-6-sl*(nn>12?5:7))%N+N)%N,ln=GU?GS[sl][1]:sl%2?-3.2:3.2,")
rep("if(PIT&&PIT.real){const pn0=TG.children.length","if(PIT&&PIT.real&&!TRACKS[i].scn){const pn0=TG.children.length")
open('menu/index.v82.html','w',encoding='utf8').write(new)
cv=lambda X:np.hypot(*np.diff(np.r_[X,X[:1]],axis=0).T).sum()
print('len',cv(Q),'Q0',Q[0])
