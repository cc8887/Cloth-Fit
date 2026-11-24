"""Preserve V2's vertex/face/UV indices for a structured and broadly cut V4 coat.

Example: blender -b -t 2 --python structure_coat.py -- --chest .34 --waist .37 --abdomen .33 --hem .18 --sleeve .24
Fractions are source-geometric radial adjustments (not prescribed fit distances).
"""
import sys,argparse,pathlib,json,math,collections,shutil
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--waist',type=float,default=.37,help='transverse waist/additional body width')
P.add_argument('--abdomen',type=float,default=.33,help='front/back abdomen expansion')
P.add_argument('--sleeve','--sleeves',type=float,default=.24,help='forearm and outer sleeve radial expansion')
P.add_argument('--hem',type=float,default=.18,help='lower hem outward expansion')
P.add_argument('--chest',type=float,default=.34,help='outward upper-chest ease, preserving shoulder cap and neck')
P.add_argument('--structure',type=float,default=.68,help='localized smoothing amplitude (0 to 1 on prefit shell)')
P.add_argument('--base',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/'coat-v2')
P.add_argument('--out',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
A=P.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert 0<=A.structure<=1
for n in ('waist','abdomen','sleeve','hem','chest'):
 assert 0<=getattr(A,n)<=.55,f'{n}: choose a value in [0,.55]'
base=A.base.resolve(); out=A.out.resolve(); out.mkdir(parents=True,exist_ok=True)
assert out!=base
lines=(base/'garment.obj').read_text().splitlines()
v=[]; f=[]
for l in lines:
 if l.startswith('v '):v.append(Vector(tuple(map(float,l.split()[1:4]))))
 if l.startswith('f '):f.append(tuple(int(s.split('/')[0])-1 for s in l.split()[1:]))
edge=collections.Counter(tuple(sorted((p[k-1],p[k]))) for p in f for k in range(3))
bound=collections.defaultdict(list); adj=collections.defaultdict(set)
for (a,b),n in edge.items():
 adj[a].add(b); adj[b].add(a)
 if n==1:bound[a].append(b);bound[b].append(a)
 assert n in (1,2)
assert all(len(k)==2 for k in bound.values())
loops=[]
todo=set(bound)
while todo:
 stack=[next(iter(todo))]; rr=[]
 while stack:
  i=stack.pop()
  if i not in todo:continue
  todo.remove(i);rr.append(i);stack+=bound[i]
 loops.append(rr)
assert sorted(map(len,loops))==[18,18,36,36]
N=21.013308
y0=-.025
def ss(a,b,x):
 t=min(1,max(0,(x-a)/(b-a))); return t*t*(3-2*t)
def distance_from(ids,depth):
 d={i:0 for i in ids}; front=set(ids)
 for k in range(1,depth+1):
  front=set().union(*(adj[i] for i in front))-d.keys()
  d.update({i:k for i in front})
 return d
skel=(base/'source_skeleton.obj').read_text()
sv=[Vector(tuple(map(float,l.split()[1:4]))) for l in skel.splitlines() if l.startswith('v ')]
sides=[]
for l in loops:
 if len(l)!=18:continue
 ctr=sum((v[i] for i in l),Vector((0,0,0)))/len(l)
 axis=(sv[5]-sv[4] if ctr.x>N else sv[7]-sv[8]).normalized()
 sides.append((ctr,axis,distance_from(l,24)))
new=[]; masks=[]; fair=[]
for i,p in enumerate(v):
 x,y,z=p; xx=x-N; yy=y-y0
 shell=1-ss(.235,.424,abs(xx))
 cuff=0.; ds=Vector((0,0,0))
 for ctr,axis,levels in sides:
  k=levels.get(i,99); u=(p-ctr).dot(axis); along=ctr+axis*u
  w=(1-ss(2,23,k))*ss(.235,.42,abs(xx))
  if w>cuff:
   cuff=w; ds=(p-along)*w
 tor=shell*(1-cuff)
 # Chest and abdomen overlap complementary height weights to prevent an hourglass waist.
 waist=ss(-.64,-.17,z)*(1-ss(.25,.53,z))*tor
 belly=ss(-.66,-.19,z)*(1-ss(.23,.48,z))*tor
 chest=ss(.17,.39,z)*(1-ss(.485,.655,z))*tor
 # Keep shoulder cap at z >= .655; carry a continuous wide A-line toward the rim.
 hem=1-ss(-.74,-.19,z)
 bx=A.waist*waist+A.chest*chest
 by=A.abdomen*belly*(1.12 if yy<0 else .93)+A.chest*chest*(1.17 if yy<0 else .94)
 q=Vector((N+xx*(1+A.waist*waist+A.hem*hem)+math.copysign(.14*A.chest*chest*ss(.05,.20,abs(xx)),xx),
           y0+yy*(1+by+A.hem*.73*hem),z))+ds*A.sleeve
 new.append(q)
 # Larger cut begins at the chest. Preserve neck/shoulder anchors and IPC on every triangle.
 if (z<.528 and shell>.52) or cuff>.39 or (z>.84 and abs(xx)<.195):
  masks.append(i)
 fair.append(max(tor*(1-ss(.48,.631,z))*ss(-.732,-.68,z),
                 cuff*ss(.05,.13,z)*(1-ss(.37,.53,z))))
# Fair only the surface around chest/torso/outer sleeves; retain sewn edges and shoulder cap.
boundary=set(bound)
for _ in range(10):
 nxt=list(new)
 for i,q in enumerate(new):
  w=fair[i]*.57*A.structure
  if i in boundary or w<1e-6:continue
  near=sum((new[j] for j in adj[i]),Vector((0,0,0)))/len(adj[i])
  d=near-q
  nxt[i]=q+Vector((d.x,d.y,.30*d.z))*w
 new=nxt
for i,k in enumerate(loops):
 if len(k)==36 and sum(v[j].z for j in k)/36>.8:
  assert max((v[j]-new[j]).length for j in k)<1e-8
tree=BVHTree.FromPolygons(new,f,all_triangles=True)
hits={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a<b and not set(f[a]).intersection(f[b])}
areas=[(new[b]-new[a]).cross(new[c]-new[a]).length*.5 for a,b,c in f]
stack=[0]; seen=set()
while stack:
 i=stack.pop()
 if i in seen:continue
 seen.add(i);stack.extend(adj[i]-seen)
assert len(seen)==len(new)
assert min(areas)>1e-8
if hits:print('HIT_COORDS', [[tuple(sum((new[j] for j in f[i]),Vector((0,0,0)))/3) for i in pp] for pp in sorted(hits)[:15]])
assert not hits,f'non-adjacent self-intersections: {len(hits)}; reduce expansion'
idx=0
with (out/'garment.obj').open('w') as io:
 for l in lines:
  if l.startswith('v '):
   io.write('v %.9f %.9f %.9f\n'%tuple(new[idx]));idx+=1
  else:io.write(l+'\n')
assert idx==len(new)
(out/'source_skeleton.obj').write_text(skel)
(out/'no-fit.txt').write_text(' '.join(map(str,masks))+'\n')
bpy.ops.wm.open_mainfile(filepath=str(base/'cloud_coat.blend'))
obj=next(o for o in bpy.data.objects if o.name.startswith('Cloud coat · outer shell'))
assert len(obj.data.vertices)==len(new)
for vert,p in zip(obj.data.vertices,new):vert.co=p
obj['ease_params']=json.dumps({k:getattr(A,k) for k in ('waist','abdomen','sleeve','hem','chest','structure')})
obj['design_notes']='Cloud coat v4: broadened chest and stronger structured silhouette; same UV; no-fit starts from chest.'
obj.data.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'cloud_coat.blend'))
def widths(zmin,zmax):
 ids=[i for i,p in enumerate(v) if zmin<=p.z<zmax and abs(p.x-N)<.315]
 def mm(coords):return [round(max(coords[i][j] for i in ids)-min(coords[i][j] for i in ids),6) for j in (0,1)]
 before,after=[mm(p) for p in (v,new)]
 return {'before':before,'after':after,'fraction':[round(a/b-1,4) for a,b in zip(after,before)]}
info=dict(vertices=len(new),faces=len(f),boundary_loops=sorted(map(len,loops)),components=1,nonadjacent_static_self_intersections=0,minimum_triangle_area=min(areas),vertex_face_uv_correspondence='v2 faces and OBJ vt tokens are preserved verbatim; only v coordinates vary',profile={k:getattr(A,k) for k in ('waist','abdomen','sleeve','hem','chest','structure')},source_cross_section_xy={'chest':widths(.402,.545),'waist':widths(.04,.18),'abdomen':widths(.19,.32),'lower_hem':widths(-.74,-.58)},no_fit_vertex_count=len(masks),no_fit_face_count=sum(set(t)<=set(masks) for t in f))
(out/'geometry.json').write_text(json.dumps(info,indent=2)+'\n')
zones={k:[] for k in ('collar','shoulders','chest','waist','abdomen','sleeves','hem')}
for i,(x,y,z) in enumerate(v):
 ax=abs(x-N)
 reach=min(levels.get(i,99) for _,_,levels in sides)
 if z>.82 and ax<.195: q='collar'
 elif .56<z<.74 and .17<ax<.305 and reach>23: q='shoulders'
 elif .39<z<.54 and ax<.27 and reach>23:q='chest'
 elif -.01<z<.18 and ax<.29: q='waist'
 elif .19<z<.33 and ax<.29: q='abdomen'
 elif reach<=13 and ax>.42 and z>-.20: q='sleeves'
 elif z<-.55: q='hem'
 else:continue
 zones[q].append(i)
(out/'zone_indices.json').write_text(json.dumps({'indexing':'zero-based OBJ vertex order; classified in v2 source rest coordinates and valid on topology-compatible solves','indices':zones},separators=(',',':'))+'\n')
print('ZONE_COUNTS',{k:len(a) for k,a in zones.items()})
print('LOOSE_QA',json.dumps(info))
