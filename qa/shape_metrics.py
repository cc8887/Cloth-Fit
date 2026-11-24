"""Compare fixed material regions of matched Cloth-fit outputs. Not cloth stiffness measurement."""
from pathlib import Path
from collections import defaultdict
import argparse,json
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('zone_json',type=Path)
p.add_argument('v3',type=Path)
p.add_argument('v4',type=Path)
a=p.parse_args()
def obj(p):
 v=[]; f=[]
 for line in p.open():
  s=line.split()
  if not s:continue
  if s[0]=='v':v.append([float(x) for x in s[1:4]])
  if s[0]=='f':f.append([int(x.partition('/')[0])-1 for x in s[1:]])
 return np.array(v),np.array(f)
V,F=obj(a.v3)
W,G=obj(a.v4)
assert V.shape==W.shape and np.array_equal(F,G)
z=json.loads(a.zone_json.read_text())['indices']
ed=defaultdict(list)
for i,(x,y,zx) in enumerate(F):
 for e in [(x,y),(y,zx),(zx,x)]:ed[tuple(sorted(e))].append(i)
def nrm(v):
 tri=v[F]
 n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
 norm=np.linalg.norm(n,axis=1)
 if min(norm)<1e-14:raise ValueError('Degenerate surface')
 return n/norm[:,None]
nv,nw=nrm(V),nrm(W)
out={'note':'Matched vertex regions in geometry, axis extents and adjacent triangle angles; static shape diagnostic, not textile stiffness','regions':{}}
for name,items in z.items():
 ids=list(dict.fromkeys(items)); lookup=set(ids)
 if not ids:continue
 de=[f for (i,j),f in ed.items() if i in lookup and j in lookup and len(f)==2]
 def sample(nr):
  if not de:return None
  d=np.array(de)
  angles=np.rad2deg(np.arccos(np.clip(np.sum(nr[d[:,0]]*nr[d[:,1]],axis=1),-1,1)))
  return [round(float(x),3) for x in np.percentile(angles,[50,90])]
 out['regions'][name]={'vertex_count':len(ids),'axis_extent_v3':np.ptp(V[ids],axis=0).round(6).tolist(),'axis_extent_v4':np.ptp(W[ids],axis=0).round(6).tolist(),
                       'adjacent_face_angle_degrees_p50_p90_v3':sample(nv),'adjacent_face_angle_degrees_p50_p90_v4':sample(nw)}
print(json.dumps(out,indent=2))
