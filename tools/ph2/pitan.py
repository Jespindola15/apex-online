import numpy as np,json,struct
ac=np.load('monza/ac_pts.npy')[:,[0,2]];g=np.load('monza/ac_xz_old.npy')
mu1,mu2=ac.mean(0),g.mean(0);H=(ac-mu1).T@(g-mu2);U,S,Vt=np.linalg.svd(H);R=Vt.T@U.T
print('det',np.linalg.det(R),'fit err',np.hypot(*((ac-mu1)@R.T+mu2-g).T).max())
tf=lambda p:(np.asarray(p)-mu1)@R.T+mu2
nodes=json.load(open('/mnt/user-data/uploads/descargas2/_monza_kn5/ac_nodes.json'))
c=np.load('monza/centre_game.npy')
P=np.array(json.load(open('monza/entry.json'))['pts'])
i0=np.argmin(np.hypot(*(c-P[0]).T))
if np.dot(c[(i0+5)%len(c)]-c[i0],P[5]-P[0])<0: c=c[::-1];i0=np.argmin(np.hypot(*(c-P[0]).T))
c=np.roll(c,-i0,axis=0)
d=np.r_[0,np.cumsum(np.hypot(*np.diff(np.r_[c,c[:1]],axis=0).T))];L=d[-1]
t=np.gradient(c,axis=0);t/=np.linalg.norm(t,axis=1,keepdims=True);nm=np.c_[t[:,1]*-1,t[:,0]]  # game Nm=(-t.z,0,t.x) => (x,z)->(-tz, tx)
def proj(p):
    # nearest on dense polyline
    j=np.argmin(np.hypot(*(c-p).T));best=None
    for k in (j-1,j):
        a,b=c[k%len(c)],c[(k+1)%len(c)];ab=b-a;u=np.clip(np.dot(p-a,ab)/np.dot(ab,ab),0,1);q=a+u*ab;dd=np.hypot(*(p-q))
        if best is None or dd<best[0]:best=(dd,k%len(c),u,q)
    dd,k,u,q=best;s=d[k]+u*np.hypot(*(c[(k+1)%len(c)]-c[k]));n=nm[k]
    lat=np.dot(p-q,n);s=s if s<L/2 else s-L
    return s,lat
def grp(pre):
    ks=sorted([k for k in nodes if k.startswith(pre)],key=lambda k:int(k.split('_')[-1]) if k.split('_')[-1].isdigit() else -1)
    return ks
out={}
for pre in('AC_PIT_','AC_START_','AC_HOTLAP','AC_TIME_'):
    ks=grp(pre);print(pre,len(ks))
    for k in ks:
        n=nodes[k];p=tf([n[0],n[2]]);s,lat=proj(p);fw=tf([n[0]+n[3][0],n[2]+n[3][2]])-p;hd=np.degrees(np.arctan2(fw[1],fw[0]))
        out[k]=(round(float(s),1),round(float(lat),1),round(float(p[0]),1),round(float(p[1]),1))
        print(' ',k,'s=%.1f lat=%.1f'%(s,lat),'pos',p.round(1),'ydir-fw',[round(x,2) for x in n[3]])
json.dump(out,open('ph2/nodes_sl.json','w'))
print('L',L)

# ---- pit_lane.ai
d0=open('/mnt/user-data/uploads/descargas2/_monza_tmp/monza/2022/ai/pit_lane.ai','rb').read()
ver,n,lt,sc=struct.unpack('<4i',d0[:16])
pp=np.frombuffer(d0,dtype='<f4',count=n*5,offset=16).reshape(n,5)
ex=np.frombuffer(d0,dtype='<f4',count=n*18,offset=16+n*20+4).reshape(n,18)
q=tf(pp[:,[0,2]].astype(float));sl_=np.array([proj(x) for x in q])
print('pit_lane.ai n',n,'len',np.hypot(*np.diff(q,axis=0).T).sum())
for k in list(range(0,n,60))+[n-1]:print(k,'s=%.1f lat=%.1f'%tuple(sl_[k]),'speed?',ex[k,0].round(1),'sides',ex[k,5].round(1),ex[k,6].round(1),'y',pp[k,1].round(2))
np.save('ph2/pitlane_sl.npy',np.c_[sl_,q,pp[:,1],ex[:,5],ex[:,6]])
