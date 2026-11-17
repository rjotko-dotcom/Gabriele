# Hidden-line drawing engine: cut lines + visible feature edges per view
import sys, json, numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
S=sys.argv[sys.argv.index('--')+1]; which=sys.argv[sys.argv.index('--')+2:]
g=np.load(S+'/geo.npz'); V=g['V'].astype(float); T=g['T']; O=g['O']; names=list(g['names'])
SHELL={'a1_erdve1','Lubos1','G_1_variantas_sienele1'}
BLOB={'Olive_Tree____Plant1','ARRANJO_VASOS_05_1'}
oname=np.array(names)[O]
isshell=np.isin(oname,list(SHELL)); isblob=np.isin(oname,list(BLOB))
# weld
key=np.round(V/0.0005).astype(np.int64)
_,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel()
VW=np.zeros((inv.max()+1,3)); VW[inv]=V; TW=inv[T]
P=VW[TW]; N=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]); A=np.linalg.norm(N,axis=1); ok=A>1e-12
N[ok]/=A[ok,None]
print('bvh...',flush=True)
bvh=BVHTree.FromPolygons([tuple(v) for v in VW],[tuple(t) for t in TW[ok]],epsilon=0.0)
# edges with adjacency
E=np.concatenate([TW[:,[0,1]],TW[:,[1,2]],TW[:,[2,0]]]); F=np.tile(np.arange(len(TW)),3)
E.sort(1); ord_=np.lexsort((E[:,1],E[:,0])); E=E[ord_]; F=F[ord_]
brk=np.r_[True,(np.diff(E,axis=0)!=0).any(1)]; gid=np.cumsum(brk)-1
ng=gid.max()+1; UE=E[brk]; cnt=np.bincount(gid)
first=F[brk]; second=np.full(ng,-1); m2=~brk; second[gid[m2]]=F[m2]
print('edges',ng,flush=True)
def views():
    return {
     'PLAN':dict(axis=2,sign=-1,cut=1.2,u=lambda p:p[:,0],v=lambda p:p[:,1]),
     'A':dict(axis=1,sign=+1,cut=5.35,u=lambda p:p[:,0],v=lambda p:p[:,2]),
     'B':dict(axis=1,sign=-1,cut=4.00,u=lambda p:-p[:,0],v=lambda p:p[:,2]),
     'C':dict(axis=0,sign=-1,cut=6.00,u=lambda p:p[:,1],v=lambda p:p[:,2]),
     'D':dict(axis=0,sign=+1,cut=14.25,u=lambda p:-p[:,1],v=lambda p:p[:,2]),
    }
def run(name,vw):
    ax,sg,c=vw['axis'],vw['sign'],vw['cut']
    depth=lambda p:(p[...,ax]-c)*sg          # >0 beyond cut (away from viewer)
    out={'cut_shell':[],'cut_obj':[],'vis':[],'blob':[],'above':[]}
    # 1 cut segments
    d=depth(P); s=np.sign(d); cross=(s.min(1)<0)&(s.max(1)>0)&ok
    for ti in np.where(cross)[0]:
        pts=[]
        for a,b in ((0,1),(1,2),(2,0)):
            da,db=d[ti,a],d[ti,b]
            if (da<0)!=(db<0):
                t=da/(da-db); pts.append(P[ti,a]+(P[ti,b]-P[ti,a])*t)
        if len(pts)==2:
            pp=np.array(pts); seg=np.c_[vw['u'](pp),vw['v'](pp)].tolist()
            (out['cut_shell'] if isshell[ti] else out['cut_obj']).append(seg)
    # 2 feature edges
    viewdir=np.zeros(3); viewdir[ax]=sg      # direction viewer looks
    f1=first; f2=second
    n1=N[f1]; n2=np.where((f2>=0)[:,None],N[np.maximum(f2,0)],0)
    dih=np.einsum('ij,ij->i',n1,n2)
    bnd=(f2<0)
    crease=(~bnd)&(dih<np.cos(np.radians(28)))
    s1=np.sign(n1@viewdir); s2=np.sign(n2@viewdir)
    sil=(~bnd)&(s1!=s2)&(dih<np.cos(np.radians(6)))
    sel=(bnd|crease|sil)&~isblob[f1]&(oname[f1]!='MARY_MADE_1_1')
    EE=UE[sel]; obj_of=O[f1[sel]]
    p0=VW[EE[:,0]]; p1=VW[EE[:,1]]
    d0=depth(p0); d1=depth(p1)
    keep=(d0>-1e-6)|(d1>-1e-6)
    # clip to beyond side
    p0=p0[keep];p1=p1[keep];d0=d0[keep];d1=d1[keep]
    t=np.clip(np.where(d0<0,d0/(d0-d1+1e-15),0),0,1); q0=p0+(p1-p0)*t[:,None]
    t=np.clip(np.where(d1<0,d1/(d1-d0+1e-15),0),0,1); q1=p1+(p0-p1)*t[:,None]
    toview=Vector(tuple(-viewdir))
    L=np.linalg.norm(q1-q0,axis=1); nonzero=L>1e-4
    q0=q0[nonzero];q1=q1[nonzero];L=L[nonzero]
    print(name,'edges to test',len(q0),flush=True)
    step=0.006
    segs=[]
    for a,b,l in zip(q0,q1,L):
        n=max(2,int(l/step)+1)
        ts=np.linspace(0,1,n); pts=a+(b-a)*ts[:,None]
        vis=np.empty(n,bool)
        for k,p in enumerate(pts):
            dd=(p[ax]-c)*sg
            o=Vector(p)+toview*0.002
            hit=bvh.ray_cast(o,toview,max(dd-0.002,0))
            vis[k]=hit[0] is None
        # runs
        k=0
        while k<n:
            if vis[k]:
                j=k
                while j+1<n and vis[j+1]: j+=1
                if j>k or n==2:
                    seg=np.array([pts[k],pts[j]]); segs.append((seg,float(np.mean(depth(seg)))))
                k=j+1
            else: k+=1
    for seg,dep in segs:
        out['vis'].append([np.c_[vw['u'](seg),vw['v'](seg)].tolist(),dep])
    # 3 blob outlines (tree, flowers)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from scipy import ndimage
    for bn in BLOB:
        m=(oname==bn)
        pts=P[m].reshape(-1,3)
        if name!='PLAN': pts=pts[depth(pts)>0]
        if len(pts)==0: continue
        uv=np.c_[vw['u'](pts),vw['v'](pts)]; r=0.012
        mn=uv.min(0)-0.05; idx=((uv-mn)/r).astype(int); sh=idx.max(0)+3
        img=np.zeros(sh[::-1]); img[idx[:,1],idx[:,0]]=1
        img=ndimage.binary_closing(ndimage.binary_dilation(img,iterations=2),iterations=3)
        cs=plt.contour(np.arange(sh[0])*r+mn[0],np.arange(sh[1])*r+mn[1],img.astype(float),levels=[0.5])
        for path in cs.allsegs[0]:
            if len(path)>8: out['blob'].append(path[::2].tolist())
        plt.close('all')
    if name=='PLAN':
        from scipy.spatial import ConvexHull
        for nm in ['Nuleidimas1_1','Nuleidimas2_1','Neleidimas3_1']:
            pts=P[oname==nm].reshape(-1,3); uv=np.c_[pts[:,0],pts[:,1]]
            h=ConvexHull(uv); out['above'].append(uv[h.vertices].tolist()+[uv[h.vertices[0]].tolist()])
    json.dump(out,open(f'{S}/draw_{name}.json','w'))
    print(name,{k:len(v) for k,v in out.items()},flush=True)
for nm,vw in views().items():
    if not which or nm in which: run(nm,vw)
