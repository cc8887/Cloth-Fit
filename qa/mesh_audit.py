import argparse, collections as c, json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('obj',nargs='+',type=Path)
args=p.parse_args()
def read(path):
    v=[]; f=[]; vt=[]; ft=[]
    for line in path.open():
        fields=line.split()
        if not fields: continue
        if fields[0]=='v': v.append([float(x) for x in fields[1:4]])
        elif fields[0]=='vt': vt.append([float(x) for x in fields[1:3]])
        elif fields[0]=='f':
            triples=[(x.split('/')+['',''])[:3] for x in fields[1:]]
            def idx(x,n):return int(x)-1 if int(x)>0 else n+int(x)
            f.append(tuple(idx(a,len(v)) for a,b,_ in triples))
            ft.append(tuple(idx(b,len(vt)) if b else -1 for a,b,_ in triples))
    return np.array(v),f,np.array(vt),ft
def comp(graph):
    remain=set(graph); n=0; sizes=[]
    while remain:
        n+=1; size=0; q=[remain.pop()]
        while q:
            size+=1
            a=q.pop()
            nxt=remain.intersection(graph[a]); remain.difference_update(nxt); q.extend(nxt)
        sizes.append(size)
    return n,sorted(sizes,reverse=True)
def audit(path, ref=None):
    v,f,vt,ft=read(path)
    tri=all(len(face)==3 for face in f)
    e=c.Counter(tuple(sorted((a,b))) for F in f for a,b in zip(F,F[1:]+F[:1]))
    boundary=c.defaultdict(set); graph=c.defaultdict(set)
    for (a,b),k in e.items():
        graph[a].add(b);graph[b].add(a)
        if k==1: boundary[a].add(b);boundary[b].add(a)
    t=np.array(f) if tri else None
    areas=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)*.5 if tri else None
    same_top=ref is not None and f==ref[1]
    other={} if ref is None else {'same_faces_as_source':same_top, 'same_uv_topology_as_source':ft==ref[3]}
    return {'obj':path.name,'vertices':len(v),'faces':len(f),'triangulated':tri, 'unused_vertices':len(v)-len(graph),'connected_components':comp(graph)[0],'boundary_components':comp(boundary)[0],'boundary_valid_loops':all(len(s)==2 for s in boundary.values()),'nonmanifold_edges':sum(k>2 for k in e.values()),'near_zero_area_triangles':int(np.count_nonzero(areas<1e-13)) if areas is not None else None,'coordinate_bounds':np.round([v.min(0),v.max(0)],5).tolist(),'face_corner_uv_complete':len(vt)>0 and all(0<=u<len(vt) for F in ft for u in F),**other}
ref=read(args.obj[0])
print(json.dumps([audit(x, None if i==0 else ref) for i,x in enumerate(args.obj)],ensure_ascii=False,indent=2))
