import sys,json,struct,numpy as np
src,dst,frac,intfrac=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
f=open(src,'rb').read();l=struct.unpack('<I',f[12:16])[0];j=json.loads(f[20:20+l]);B=f[20+l+8:]
def acc(i):
    a=j['accessors'][i];bv=j['bufferViews'][a['bufferView']];n=a['count']
    nc={'VEC3':3,'VEC2':2,'SCALAR':1,'VEC4':4}[a['type']]
    dt={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]
    off=bv.get('byteOffset',0)+a.get('byteOffset',0);st=bv.get('byteStride',0)
    sz=np.dtype(dt).itemsize*nc
    if st and st!=sz:return np.frombuffer(B,dtype=np.uint8,count=st*n,offset=off).reshape(n,st)[:,:sz].copy().view(dt).reshape(n,nc)
    return np.frombuffer(B,dtype=dt,count=n*nc,offset=off).reshape(n,nc)
def cluster(P,N,U,I,cell):
    k=np.floor(P.astype(np.float64)/cell).astype(np.int64);kk=(k[:,0]*73856093)^(k[:,1]*19349663)^(k[:,2]*83492791)
    _,first,inv=np.unique(kk,return_index=True,return_inverse=True)
    nc=len(first);cnt=np.bincount(inv,minlength=nc).astype(np.float64)
    Pm=np.zeros((nc,3));Nm=np.zeros((nc,3))
    for a in range(3):Pm[:,a]=np.bincount(inv,weights=P[:,a],minlength=nc)/cnt;Nm[:,a]=np.bincount(inv,weights=N[:,a],minlength=nc)
    Nm/=np.maximum(np.linalg.norm(Nm,axis=1,keepdims=True),1e-9)
    I2=inv[I];ok=(I2[:,0]!=I2[:,1])&(I2[:,1]!=I2[:,2])&(I2[:,0]!=I2[:,2]);return Pm.astype(np.float32),Nm.astype(np.float32),U[first],I2[ok]
bin_=bytearray();views=[];accs=[]
def addview(b,target=None):
    while len(bin_)%4:bin_.append(0)
    off=len(bin_);bin_.extend(b);v=dict(buffer=0,byteOffset=off,byteLength=len(b))
    if target:v['target']=target
    views.append(v);return len(views)-1
def addacc(arr,ct,typ,target,mm=False):
    v=addview(arr.tobytes(),target);d=dict(bufferView=v,componentType=ct,count=int(len(arr)),type=typ)
    if mm:d['min']=[float(x) for x in arr.min(0)];d['max']=[float(x) for x in arr.max(0)]
    accs.append(d);return len(accs)-1
tot0=tot1=0
for m in j['meshes']:
    for p in m['primitives']:
        mat=j['materials'][p['material']]['name'] if 'material' in p else ''
        P=acc(p['attributes']['POSITION']).astype(np.float32);N=acc(p['attributes']['NORMAL']).astype(np.float32);U=acc(p['attributes']['TEXCOORD_0']).astype(np.float32);I=acc(p['indices'])[:,0].astype(np.int64).reshape(-1,3)
        n0=len(I);tot0+=n0
        isint=mat.lower().startswith('int')
        fr=intfrac if isint else frac
        if fr<=0:
            P2=P[:1].repeat(3,0);N2=N[:1].repeat(3,0);U2=U[:1].repeat(3,0);I2=np.array([[0,1,2]])
            P2=P[:3]*0+P[:1];I2=np.array([[0,0,0]]);P2=P[:1];N2=N[:1];U2=U[:1]
        elif n0>600:
            tgt=max(250,n0*fr);cell=.004;P2,N2,U2,I2=P,N,U,I
            while len(I2)>tgt and cell<.6:
                cell*=1.25;P2,N2,U2,I2=cluster(P,N,U,I,cell)
        else:P2,N2,U2,I2=P,N,U,I
        vs,inv=np.unique(I2,return_inverse=True);P2=P2[vs];N2=N2[vs];U2=U2[vs];I2=inv.reshape(-1,3)
        nn=np.linalg.norm(N2,axis=1,keepdims=True);N2=N2/np.maximum(nn,1e-6)
        tot1+=len(I2)
        p['attributes']=dict(POSITION=addacc(P2.astype(np.float32),5126,'VEC3',34962,True),NORMAL=addacc(N2.astype(np.float32),5126,'VEC3',34962),TEXCOORD_0=addacc(U2.astype(np.float32),5126,'VEC2',34962))
        p['indices']=addacc(I2.reshape(-1).astype(np.uint32 if len(P2)>65535 else np.uint16),5125 if len(P2)>65535 else 5123,'SCALAR',34963)
for im in j['images']:
    bv=j['bufferViews'][im['bufferView']];b=B[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']];im['bufferView']=addview(bytes(b))
j['accessors']=accs;j['bufferViews']=views;j['buffers']=[dict(byteLength=len(bin_))]
js=json.dumps(j,separators=(',',':')).encode()
while len(js)%4:js+=b' '
while len(bin_)%4:bin_.append(0)
open(dst,'wb').write(struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(bin_))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(bin_),b'BIN\0')+bytes(bin_))
import os;print(dst,tot0,'->',tot1,os.path.getsize(dst)/1e6,'MB')
