import numpy as np,collections
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def components(I,nv):
    r=np.r_[I[:,0],I[:,1]];c=np.r_[I[:,1],I[:,2]]
    g=coo_matrix((np.ones(len(r)),(r,c)),shape=(nv,nv));nc,lab=connected_components(g,directed=False)
    comp=lab[I[:,0]];order=np.argsort(comp,kind='stable');cs=comp[order]
    return np.split(order,np.flatnonzero(np.diff(cs))+1)
def kabsch(A,B):
    # find R,t so that R@A+t ~ B (A,B Nx3, centered handled)
    ca=A.mean(0);cb=B.mean(0);H=(A-ca).T@(B-cb);U,S,Vt=np.linalg.svd(H)
    d=np.sign(np.linalg.det(Vt.T@U.T));D=np.diag([1,1,d]);R=Vt.T@D@U.T
    return R,cb-R@ca
def find_instances(P,N,U,I,tmin=6,tmax=320,mincopies=4,tol=0.03):
    """returns list of groups: dict(ref=(Pl,Nl,Ul,Il), mats=[4x4 (R,t)], tri_idx=set of triangle indices consumed)"""
    groups=components(I,len(P));sig=collections.defaultdict(list)
    for gi in groups:
        if not(tmin<=len(gi)<=tmax):continue
        tr=I[gi];vs=np.unique(tr);Pv=P[vs].astype(np.float64);Uv=U[vs]
        c=Pv.mean(0);d=np.linalg.norm(Pv-c,axis=1)
        key=np.lexsort((np.round(d,2),np.round(Uv[:,1],3),np.round(Uv[:,0],3)))
        s=(len(gi),len(vs),hash(np.round(Uv[key],3).tobytes()),hash(np.round(d[key],1).tobytes()))
        sig[s].append((gi,vs,key,c))
    out=[]
    for s,lst in sig.items():
        if len(lst)<mincopies:continue
        gi0,vs0,key0,c0=lst[0]
        A=P[vs0][key0].astype(np.float64)
        # reference local mesh: vertices ordered by vs0 order (keep original order); map via rank
        ok=[]
        for gi,vs,key,c in lst:
            Bv=P[vs][key].astype(np.float64)
            R,t=kabsch(A,Bv)
            res=np.abs((A@R.T+t)-Bv).max()
            if res<=tol and np.abs(np.linalg.det(R)-1)<1e-3:ok.append((gi,R,t))
        if len(ok)<mincopies:continue
        # reference mesh local coords around c0 (use ref vertices in vs0 order)
        pos0=vs0;rm={v:i for i,v in enumerate(vs0)}
        Pl=(P[vs0]-c0).astype(np.float32);Nl=N[vs0].astype(np.float32);Ul=U[vs0].astype(np.float32)
        Il=np.vectorize(rm.get)(I[gi0]).astype(np.int64)
        mats=[]
        for gi,R,t in ok:
            # instance maps local (P - c0) -> world: x = R@(p+c0)+t = R@p + (R@c0+t)
            mats.append((R,R@c0+t))
        out.append(dict(Pl=Pl,Nl=Nl,Ul=Ul,Il=Il,mats=mats,tris=np.concatenate([gi for gi,_,_ in ok])))
    return out
