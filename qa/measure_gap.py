"""Compare per-zone matched OBJ vertex clearance in identical avatar coordinates.

Run with Blender --python and pass old_dir new_dir zone_vertices.json output.json.
Clearance is unsigned nearest triangle distance: not a collision or containment test.
Distances are converted to percentage of the longest normalized skeleton extent (2).
"""
import json,sys,statistics
from pathlib import Path
from mathutils.bvhtree import BVHTree
A,B,Z,O=map(Path,sys.argv[sys.argv.index('--')+1:])

def obj(p):
    v=[]; f=[]
    for l in p.open():
        x=l.split()
        if not x: continue
        if x[0]=='v': v.append(tuple(map(float,x[1:4])))
        if x[0]=='f': f.append(tuple(int(t.split('/')[0])-1 for t in x[1:]))
    return v,f

av,af=obj(A/'avatar.obj')
bv,bf=obj(B/'avatar.obj')
assert av==bv and af==bf, 'body changed; cannot compare matched gaps'
la,fa=obj(A/'garment_final.obj'); lb,fb=obj(B/'garment_final.obj')
assert fa==fb and len(la)==len(lb), 'garment topology mismatch'
tree=BVHTree.FromPolygons(av,af,all_triangles=True)
zones=json.loads(Z.read_text())["indices"]
def extent(v, ids, axis):
    a=[v[i][axis] for i in ids]
    return round((max(a)-min(a))*50.,4)

def distance(v):
    q=tree.find_nearest(v)
    if q[3] is None: raise RuntimeError('No nearest surface')
    return q[3]*50.

da=list(map(distance,la)); db=list(map(distance,lb))
out={"unit":"percent longest normalized skeleton span","same_avatar":True,"same_cloth_topology":True,"axis_extents":"world-normalized OBJ X width, Y depth, Z height; same units","zones":{}}
for name,indices in zones.items():
    ix=sorted(set(indices))
    if not ix: continue
    ao=[da[i] for i in ix];bo=[db[i] for i in ix]; d=[y-x for x,y in zip(ao,bo)]
    out["zones"][name]={"matched_vertices":len(ix),"baseline_median":round(statistics.median(ao),4),
                       "baseline_bbox_xyz":[extent(la,ix,j) for j in range(3)],
                       "variant_bbox_xyz":[extent(lb,ix,j) for j in range(3)],
                       "loose_median":round(statistics.median(bo),4),
                       "paired_change_median":round(statistics.median(d),4),
                       "proportion_increased":round(sum(x>0.005 for x in d)/len(d),4),
                       "baseline_p10":round(statistics.quantiles(ao,n=10)[0],4) if len(ix)>1 else None,
                       "loose_p10":round(statistics.quantiles(bo,n=10)[0],4) if len(ix)>1 else None}
O.write_text(json.dumps(out,indent=2)+"\n")
