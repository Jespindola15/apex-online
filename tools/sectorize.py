import sys,json,struct,time,collections
import numpy as np
sys.path.insert(0,'.')
from glbio import *
from inst import components,kabsch
src=sys.argv[1];dst=sys.argv[2]
import os
CELL=200.0;CELLB=float(os.environ.get("CELLB","10000000"));MAXEA=120.0;MAXEB=min(300.0,CELLB);LIGHT=int(os.environ.get("LIGHT","25000"));MINCOP=60
ALWAYS={'horizont'}
ORG={'trees','trees_001','tree8','branch5','hedge','treesline','tree_shadow'}
LODC={'metals':.3,'misc1':.4,'Bark':.5,'gstand':.4,'serraglio2022':.5,'serraglio2':.5,'SERRAGLIO':.5,'box':.4,'box_M':.4}
INSTM={'metals','misc1','walls','walls26','serraglio2022','bridges','flag1','flag2','flag3','flag4','flag5','flag6','flag7','flag8','gris_tyre','gstand','apsh-shader2','box_M','drs'}
DENS=[1.0,.75,.5,.35]
rng=np.random.default_rng(7)
t0=time.time()
j,B=load(src);ps=prims(j,B)
def split_long(P,N,U,I,maxe):
    P=[P];N=[N];U=[U];n=len(P[0])
    Pa=P[0];Na=N[0];Ua=U[0]
    for it in range(12):
        a=Pa[I[:,0]];b=Pa[I[:,1]];c=Pa[I[:,2]]
        e=np.stack([np.linalg.norm(b-a,axis=1),np.linalg.norm(c-b,axis=1),np.linalg.norm(a-c,axis=1)],1)
        m=e.max(1)>maxe
        if not m.any():break
        T=I[m];keep=I[~m];k=e[m].argmax(1)
        ar=np.arange(len(T))
        v0=T[ar,k];v1=T[ar,(k+1)%3];v2=T[ar,(k+2)%3]
        mid=len(Pa)+np.arange(len(T))
        Pm=(Pa[v0]+Pa[v1])/2;Nm=Na[v0]+Na[v1];Nm/=np.maximum(np.linalg.norm(Nm,axis=1,keepdims=True),1e-9);Um=(Ua[v0]+Ua[v1])/2
        Pa=np.concatenate([Pa,Pm.astype(Pa.dtype)]);Na=np.concatenate([Na,Nm.astype(Na.dtype)]);Ua=np.concatenate([Ua,Um.astype(Ua.dtype)])
        I=np.concatenate([keep,np.stack([v0,mid,v2],1),np.stack([mid,v1,v2],1)])
    return Pa,Na,Ua,I
def cluster(P,N,U,I,cell):
    k=np.floor(P.astype(np.float64)/cell).astype(np.int64)
    kk=(k[:,0]*73856093)^(k[:,1]*19349663)^(k[:,2]*83492791)
    _,first,inv=np.unique(kk,return_index=True,return_inverse=True)
    I2=inv[I];ok=(I2[:,0]!=I2[:,1])&(I2[:,1]!=I2[:,2])&(I2[:,0]!=I2[:,2])
    return P[first],N[first],U[first],I2[ok]
def compact(P,N,U,I):
    vs,inv=np.unique(I,return_inverse=True)
    return P[vs],N[vs],U[vs],inv.reshape(-1,3)
# ---- buffer writer
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
meshes=[];nodes=[];stat=collections.Counter()
def mesh_node(name,matidx,P,N,U,I,extras):
    """returns node index; splits into multiple prims if >65535 verts"""
    extras['mi']=int(matidx)
    P,N,U,I=compact(P,N,U,I)
    prs=[]
    if len(P)<=65535:chunks=[(P,N,U,I)]
    else:
        chunks=[];ord_=np.argsort(P[I[:,0]][:,0]);I=I[ord_];step=20000
        for s in range(0,len(I),step):chunks.append(compact(P,N,U,I[s:s+step]))
    for (p,n,u,i) in chunks:
        a=dict(POSITION=addacc(p.astype(np.float32),5126,'VEC3',34962,True),NORMAL=addacc(n.astype(np.float32),5126,'VEC3',34962),TEXCOORD_0=addacc(u.astype(np.float32),5126,'VEC2',34962))
        ia=addacc(i.reshape(-1).astype(np.uint16),5123,'SCALAR',34963)
        prs.append(dict(attributes=a,indices=ia,material=matidx,mode=4))
    meshes.append(dict(name=name,primitives=prs));nodes.append(dict(name=name,mesh=len(meshes)-1,extras=extras))
    return len(nodes)-1
sectors=collections.defaultdict(list)   # (ix,iz)-> list of node ids
always=[]
sbox={}
def sec_add(key,ni,P):
    sectors[key].append(ni)
    b=sbox.setdefault(key,[1e9,1e9,-1e9,-1e9])
    b[0]=min(b[0],float(P[:,0].min()));b[1]=min(b[1],float(P[:,2].min()));b[2]=max(b[2],float(P[:,0].max()));b[3]=max(b[3],float(P[:,2].max()))
# first pass: instances
igroups={}   # sig->dict
inst_consumed={}  # prim idx -> set of tris
inst_data=[]
allinst=[]
for pi,p in enumerate(ps):
    if p['name'] not in INSTM or len(p['I'])<50:continue
    P=p['P'].astype(np.float64);N=p['N'];U=p['U'];I=p['I']
    groups=components(I,len(P));sig=collections.defaultdict(list)
    for gi in groups:
        if not(6<=len(gi)<=320):continue
        vs=np.unique(I[gi]);Pv=P[vs];Uv=U[vs];c=Pv.mean(0);d=np.linalg.norm(Pv-c,axis=1)
        key=np.lexsort((np.round(d,2),np.round(Uv[:,1],3),np.round(Uv[:,0],3)))
        s=(len(gi),len(vs),hash(np.round(Uv[key],3).tobytes()),hash(np.round(d[key],1).tobytes()))
        sig[s].append((gi,vs,key,c))
    for s,lst in sig.items():
        if len(lst)<MINCOP:continue
        gi0,vs0,key0,c0=lst[0];A=P[vs0][key0]
        copies=[]
        for gi,vs,key,c in lst:
            Bv=P[vs][key];R,t=kabsch(A,Bv)
            if np.abs((A@R.T+t)-Bv).max()<=0.03 and abs(np.linalg.det(R)-1)<1e-3:copies.append((gi,R,R@c0+t))
        if len(copies)<MINCOP:continue
        rm=-np.ones(len(P),np.int64);rm[vs0]=np.arange(len(vs0))
        allinst.append(dict(pi=pi,Pl=(P[vs0]-c0).astype(np.float32),Nl=N[vs0],Ul=U[vs0],Il=rm[I[gi0]],copies=copies))
print('instance groups',len(allinst),'copies',sum(len(g['copies']) for g in allinst),'tris',sum(len(c[0]) for g in allinst for c in g['copies']),round(time.time()-t0),flush=True)
# every copy of every kept group is instanced (one InstancedMesh per group, repacked by distance at runtime)
removed=collections.defaultdict(list)
for gid,g in enumerate(allinst):
    g['gid']=gid
    for gi,_,_ in g['copies']:removed[g['pi']].append(gi)
print('instanced groups',len(allinst),'removed tris',sum(len(x) for v in removed.values() for x in v),flush=True)
# ---- build sector meshes
for pi,p in enumerate(ps):
    nm=p['name'];P=p['P'].astype(np.float32);N=p['N'].astype(np.float32);U=p['U'].astype(np.float32);I=p['I']
    if pi in removed:
        rm=np.zeros(len(I),bool);rm[np.concatenate(removed[pi])]=True;I=I[~rm]
    if nm in ALWAYS:
        ni=mesh_node('m:'+nm,p['mat'],P,N,U,I,dict(always=1));always.append(ni);continue
    P,N,U,I=compact(P,N,U,I)
    lvl=1 if len(I)<=LIGHT else 0;cell=CELLB if lvl else CELL
    P,N,U,I=split_long(P,N,U,I,MAXEB if lvl else MAXEA)
    cen=(P[I[:,0]]+P[I[:,1]]+P[I[:,2]])/3
    cx=np.floor(cen[:,0]/cell).astype(np.int64);cz=np.floor(cen[:,2]/cell).astype(np.int64)
    kk=cx*100000+cz
    for key in np.unique(kk):
        sel=np.flatnonzero(kk==key);Is=I[sel];key2=(int(np.floor(key/100000+0.5)) if False else None)
        ix=(lvl,int(cx[sel[0]]));iz=int(cz[sel[0]])
        sp,sn,su,si=compact(P,N,U,Is)
        extras=dict(mat=nm)
        if nm in ORG:
            comps=components(si,len(sp));perm=rng.permutation(len(comps));order=[comps[q] for q in perm]
            tri=np.concatenate(order);si=si[tri]
            cum=np.cumsum([len(c) for c in order]);dr=[int(cum[np.searchsorted(cum,d*len(si))-1]*3) if d<1 else int(len(si)*3) for d in DENS]
            extras['org']=1;extras['dr']=dr
        ni=mesh_node(f'm:{nm}',p['mat'],sp,sn,su,si,extras);sec_add((ix,iz),ni,sp);stat['tris0']+=len(si)
        if nm in LODC and len(si)>=60:
            lp,ln,lu,li=cluster(sp,sn,su,si,LODC[nm])
            if len(li)<=0.75*len(si) and len(li)>0:
                lp,ln,lu,li=compact(lp,ln,lu,li)
                nj=mesh_node(f'm:{nm}',p['mat'],lp,ln,lu,li,dict(mat=nm,lod=1));sec_add((ix,iz),nj,lp);stat['tris1']+=len(li);stat['lodpairs']+=1
print('sector meshes done',round(time.time()-t0),dict(stat),flush=True)
# instanced meshes: one node per group, always list
for g in allinst:
    G=g;mat=ps[G['pi']]['mat'];im=[]
    for gi,R,t in G['copies']:im.extend([round(float(x),4) for x in [R[0,0],R[0,1],R[0,2],t[0],R[1,0],R[1,1],R[1,2],t[1],R[2,0],R[2,1],R[2,2],t[2]]])
    ni=mesh_node(f'i:{ps[G["pi"]]["name"]}#{G["gid"]}',mat,G['Pl'],G['Nl'],G['Ul'],G['Il'],dict(mat=ps[G['pi']]['name'],im=im,n=len(G['copies'])))
    always.append(ni);stat['inst']+=len(G['copies'])
# sector nodes
snodes=[]
for key,lst in sectors.items():
    b=sbox[key];nodes.append(dict(name=f'S_{key[0][0]}_{key[0][1]}_{key[1]}',children=lst,extras=dict(b=[round(x,2) for x in b],c=[key[0][0],key[0][1],key[1]])));snodes.append(len(nodes)-1)
nodes.append(dict(name='MZ',children=always+snodes,extras=dict(cell=CELL,cellB=CELLB,sectors=len(snodes),dens=DENS)));root=len(nodes)-1
# materials/images/textures copy
images=[]
for im in j['images']:
    bv=j['bufferViews'][im['bufferView']];b=B[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
    images.append(dict(bufferView=addview(bytes(b)),mimeType=im['mimeType']))
out=dict(asset=dict(version='2.0',generator='apex-sectorize'),scene=0,scenes=[dict(nodes=[root])],nodes=nodes,meshes=meshes,materials=j['materials'],accessors=accs,bufferViews=views,buffers=[dict(byteLength=len(bin_))],samplers=j['samplers'],images=images,textures=j['textures'])
js=json.dumps(out,separators=(',',':')).encode()
while len(js)%4:js+=b' '
while len(bin_)%4:bin_.append(0)
with open(dst,'wb') as f:
    f.write(struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(bin_)));f.write(struct.pack('<I4s',len(js),b'JSON'));f.write(js);f.write(struct.pack('<I4s',len(bin_),b'BIN\0'));f.write(bin_)
import os;print('wrote',dst,os.path.getsize(dst)/1e6,'MB sectors',len(snodes),'meshes',len(meshes),dict(stat),round(time.time()-t0),flush=True)
