import json,struct,numpy as np
def load(path):
    f=open(path,'rb').read()
    l=struct.unpack('<I',f[12:16])[0]
    j=json.loads(f[20:20+l]);B=f[20+l+8:]
    return j,B
def acc(j,B,i):
    a=j['accessors'][i];bv=j['bufferViews'][a['bufferView']];n=a['count']
    nc={'VEC3':3,'VEC2':2,'SCALAR':1,'VEC4':4}[a['type']]
    dt={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]
    off=bv.get('byteOffset',0)+a.get('byteOffset',0)
    return np.frombuffer(B,dtype=dt,count=n*nc,offset=off).reshape(n,nc)
def prims(j,B):
    out=[]
    for p in j['meshes'][0]['primitives']:
        m=j['materials'][p['material']]
        P=acc(j,B,p['attributes']['POSITION']);N=acc(j,B,p['attributes']['NORMAL']);U=acc(j,B,p['attributes']['TEXCOORD_0']);I=acc(j,B,p['indices'])[:,0].astype(np.int64).reshape(-1,3)
        out.append(dict(name=m['name'],mat=p['material'],P=P,N=N,U=U,I=I))
    return out
