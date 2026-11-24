"""Supplementary, distinct BVH static screen on meshes in the same coordinate system."""
import sys,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
def obj(p):
    v=[]; f=[]
    for l in Path(p).open():
        x=l.split()
        if not x: continue
        if x[0]=='v': v.append(tuple(map(float,x[1:4])))
        if x[0]=='f':
            t=[int(i.split('/')[0]) for i in x[1:]]
            f.append(tuple(i-1 if i>0 else len(v)+i for i in t))
    assert all(len(a)==3 for a in f)
    return v,f
args=sys.argv[sys.argv.index('--')+1:]
known_gap_a=BVHTree.FromPolygons([(0,0,0),(2,0,0),(0,2,0)],[(0,1,2)],all_triangles=True)
known_gap_b=BVHTree.FromPolygons([(1.2,1.2,0),(1.8,1.2,0),(1.2,1.8,0)],[(0,1,2)],all_triangles=True)
known_cross=BVHTree.FromPolygons([(.5,.5,-.5),(.5,.5,.5),(1.2,.5,0)],[(0,1,2)],all_triangles=True)
assert not known_gap_a.overlap(known_gap_b) and known_gap_a.overlap(known_cross),'BVH screen sanity failed'
v,f=obj(args[0])
b=BVHTree.FromPolygons(v,f,all_triangles=True)
sets=[set(t) for t in f]
self_hits=[(i,j) for i,j in b.overlap(b) if i<j and sets[i].isdisjoint(sets[j])]
d={'garment_self_nonadjacent_pair_count':len(self_hits),'self_examples':self_hits[:5]}
if len(args)>1:
    w,g=obj(args[1])
    b2=BVHTree.FromPolygons(w,g,all_triangles=True)
    hits=b.overlap(b2)
    d.update(garment_body_pair_count=len(hits),body_examples=hits[:5])
print(json.dumps(d,indent=2))
