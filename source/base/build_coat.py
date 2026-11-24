import bpy, bmesh, math, json, collections, pathlib, os
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Packaging adapter; mesh construction below is unchanged.
ASSET=pathlib.Path(os.environ.get('CLOTH_FIT_PUFFER', ROOT/'solver/upstream/garment-data/assets/garments/Puffer_dense'))
OUT=pathlib.Path(os.environ.get('CLOUD_COAT_OUT', pathlib.Path(__file__).resolve().parent))
N=21.013308
HEM=float(os.environ.get('COAT_HEM','-.72'))
RINGS=10 if HEM<-.5 else 6
def read_obj(p):
 v=[]; f=[]; edges=[]
 for l in p.read_text().splitlines():
  x=l.split()
  if x and x[0]=='v':v.append(Vector(tuple(map(float,x[1:4]))))
  if x and x[0]=='f':f.append(tuple(int(y.split('/')[0])-1 for y in x[1:]))
  if x and x[0]=='l':edges.append(tuple(int(y)-1 for y in x[1:]))
 return v,f,edges
v,f,_=read_obj(ASSET/'garment.obj')
sv,_,se=read_obj(ASSET/'skeleton.obj')
old=[q.copy() for q in v]; f=list(f)
ed=collections.Counter(tuple(sorted((q[i-1],q[i]))) for q in f for i in range(3))
de={ (q[i-1],q[i]) for q in f for i in range(3) if ed[tuple(sorted((q[i-1],q[i]))) ]==1}
nxt=dict(de)
loops=[]
while nxt:
 start=next(iter(nxt)); cur=start; ring=[]
 while cur in nxt:
  ring.append(cur); cur=nxt.pop(cur)
 assert cur==start
 loops.append(ring)
hem=min((l for l in loops if len(l)==36), key=lambda l:sum(v[i].z for i in l))
collar=max((l for l in loops if len(l)==36), key=lambda l:sum(v[i].z for i in l))
adj=[set() for p in v]
for a,b in ed:
 adj[a].add(b); adj[b].add(a)
def smoothstep(a,b,x):
 t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)
# Suppress baffle ridges from the starter triangle cage, keeping aperture vertices fixed.
rim=set(sum(loops,[]))
for _ in range(9):
 v=[p if i in rim else p.lerp(sum((v[j] for j in adj[i]),Vector((0,0,0)))/len(adj[i]),.54) for i,p in enumerate(v)]
# Repattern collar and sleeves via controlled distance bands from existing openings.
def distance_from_loop(r, count):
 d={i:0 for i in r}; front=set(r)
 for z in range(1,count+1):
  front=set().union(*(adj[i] for i in front))-d.keys()
  d.update({i:z for i in front})
 return d
for r in (l for l in loops if len(l)==18):
 center=sum((v[i] for i in r),Vector((0,0,0)))/len(r)
 side=1 if center.x>N else -1
 axis=(sv[5]-sv[4] if side>0 else sv[7]-sv[8]).normalized()
 for i,k in distance_from_loop(r,19).items():
  p=v[i]
  u=(p-center).dot(axis)
  c=center+axis*u
  radial=p-c
  g=1-smoothstep(0,19,k)
  # Cuff is a large circular bell. Avoid scaling the arm length.
  v[i]=c+radial*(1+1.48*g)+axis*(.025*g)
for i,k in distance_from_loop(collar,8).items():
 p=v[i]
 ang=math.atan2((p.x-N)/.142,(p.y+.064)/.154)
 c=math.cos(ang)
 t=1-smoothstep(2,8,k)
 # Near-planar top with back rim noticeably higher than center front.
 x=N+math.sin(ang)*(.152+.008*k)
 y=-.051+c*(.161+.009*k)
 z=.970+.025*c-.027*k
 p2=Vector((x,y,z))
 v[i]=p.lerp(p2,t)
# Diffuse the warped shoulder/collar transition and taper bell sleeves.
# Border rings remain exact, thereby preserving all four open edges.
dcol=distance_from_loop(collar,11)
dcuff={}
for r in (l for l in loops if len(l)==18):dcuff.update(distance_from_loop(r,13))
for sweep in range(72):
 nv=list(v)
 for i,k in dcol.items():
  w=.65*(1-smoothstep(7,11,k))
  if w>0 and k>0:
   nv[i]=v[i].lerp(sum((v[j] for j in adj[i]),Vector((0,0,0)))/len(adj[i]),w)
 for i,k in dcuff.items():
  w=.55*(1-smoothstep(9,13,k))
  if w>0 and k>0 and sweep<12:
   nv[i]=v[i].lerp(sum((v[j] for j in adj[i]),Vector((0,0,0)))/len(adj[i]),w)
 v=nv
# Sew extended skirt rings onto directed hem boundary using shared vertices.
Z0=sum(v[i].z for i in hem)/len(hem)
r0=[v[i].copy() for i in hem]
prev=hem
for k in range(1,RINGS+1):
 t=k/RINGS
 cur=[]
 for p in r0:
  ang=math.atan2((p.x-N)/.255,-(p.y+.025)/.19)
  # Stronger sideways sweep and roomy front/back; soft, low-amplitude long folds.
  groove=(.004*math.sin(7*ang)+.002*math.cos(11*ang))*t
  q=Vector((N+(p.x-N)*(1+.44*t)+math.sin(ang)*groove,
            -.025+(p.y+.025)*(1+.27*t)-math.cos(ang)*groove,
            HEM*t+Z0*(1-t)+(p.z-Z0)*(1-.55*t)+.013*t*math.cos(2*ang)))
  cur.append(len(v)); v.append(q)
 for j in range(len(prev)):
  j2=(j+1)%len(prev)
  a,b,c,d=prev[j],prev[j2],cur[j2],cur[j]
  f.extend([(b,a,d),(b,d,c)] if (k+j)%2 else [(b,a,c),(a,d,c)])
 prev=cur
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new('Cloud coat · connected triangular shell')
mesh.from_pydata(v,[],f); mesh.update()
obj=bpy.data.objects.new('Cloud coat · outer shell',mesh); bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj; obj.select_set(True)
for p in mesh.polygons:p.use_smooth=True
# Consistent outward normals after stitching. A d=+Y probe on lower torso disambiguates facing.
bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh); bm.free()
# Orient the complete connected mesh radially outward below the old jacket hem.
score=sum(p.normal.y*(p.center.y+.025)+p.normal.x*(p.center.x-N) for p in mesh.polygons if p.center.z < -.1)
if score<0:
 bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.reverse_faces(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
f=[tuple(p.vertices) for p in mesh.polygons]
# Always use the canonical OBJ vertex order; face loop indices are separate and may cross the seam.
zmin,zmax=min(p.z for p in v),max(p.z for p in v)
uv=mesh.uv_layers.new(name='Cloud Coat UV')
sleeve_faces=[]; collar_faces=[]
for p in mesh.polygons:
 x,y,z=p.center
 sleeve=abs(x-N)>.324
 if sleeve:sleeve_faces.append(p.index)
 if z>.715 and abs(x-N)<.19:collar_faces.append(p.index)
 vals=[]
 for j in p.loop_indices:
  q=v[mesh.loops[j].vertex_index]
  u=.5+math.atan2(q.x-N,-(q.y+.025))/(2*math.pi)
  w=(q.z-zmin)/(zmax-zmin)
  vals.append((u,w))
 seam=max(q[0] for q in vals)-min(q[0] for q in vals)>.5
 for j,(u,w) in zip(p.loop_indices,vals):
  if sleeve:u,w=(.18+.025*(u-.5),.52+.10*(w-.5))
  elif seam and u<.5:u+=1
  uv.data[j].uv=(u,w)
# Mat created for fallback preview. Textured material supplied separately.
mat=bpy.data.materials.new('Charcoal wool');mat.diffuse_color=(.022,.025,.034,1);mat.use_nodes=True
b=mat.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=mat.diffuse_color;b.inputs['Roughness'].default_value=.81
mesh.materials.append(mat)
smesh=bpy.data.meshes.new('Source skeleton');smesh.from_pydata(sv,se,[]);smesh.update()
sobj=bpy.data.objects.new('Source skeleton · official Puffer joint IDs',smesh);bpy.context.collection.objects.link(sobj);sobj.hide_render=True;sobj.hide_set(True)
# Recenter displayed objects without changing the canonical geometry exported below.
obj.location.x=-N;sobj.location.x=-N
if bpy.context.screen:
 for ar in bpy.context.screen.areas:
  if ar.type=='VIEW_3D':
   ar.spaces.active.region_3d.view_distance=3.3
   ar.spaces.active.region_3d.view_location=(0,0,.13)
obj['design_notes']='Reference remodel on compatible upper-shell topology; connected four-opening solve mesh; fabric motif UV does not affect collision.'
obj['source_coordinates']='Z up, front -Y; display has X offset removed independently of solver OBJ.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cloud_coat.blend'))
with (OUT/'garment.obj').open('w') as o:
 o.write('# Blender procedural refit shell; index stable\no Cloud_Coat\n')
 for q in v:o.write('v %.9f %.9f %.9f\n'%tuple(q))
 for j in range(len(mesh.loops)):
  u,w=uv.data[j].uv; o.write('vt %.8f %.8f\n'%(u,w))
 for p in mesh.polygons:o.write('f '+' '.join(f'{mesh.loops[j].vertex_index+1}/{j+1}' for j in p.loop_indices)+'\n')
with (OUT/'source_skeleton.obj').open('w') as o:
 for q in sv:o.write('v %.9f %.9f %.9f\n'%tuple(q))
 for a,b in se:o.write(f'l {a+1} {b+1}\n')
def mask(tight=False):
 ids=[]
 for i,(x,y,z) in enumerate(v):
  if z<(-.41 if tight else -.10) or (not tight and abs(x-N)>.575) or (z>.83 and abs(x-N)<.195):ids.append(i)
 return ids
for nm,tight in [('no-fit.txt',False),('no-fit-tight.txt',True)]:
 (OUT/nm).write_text(' '.join(map(str,mask(tight)))+'\n')
# Topology and self-intersection check on clean source output.
ed=collections.Counter(tuple(sorted((q[i-1],q[i]))) for q in f for i in range(3))
bgraph=collections.defaultdict(list)
for a,b in ed:
 if ed[a,b]==1:bgraph[a].append(b);bgraph[b].append(a)
assert all(len(nn)==2 for nn in bgraph.values())
bl=[]
while bgraph:
 stack=[next(iter(bgraph))]; rr=[]
 while stack:
  a=stack.pop()
  if a not in bgraph:continue
  rr.append(a);stack+=bgraph.pop(a)
 bl.append(len(rr))
from mathutils.bvhtree import BVHTree
tree=BVHTree.FromPolygons(v,f,all_triangles=True)
hits={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a<b and not set(f[a]).intersection(f[b])}
info=dict(vertices=len(v),faces=len(f),edge_multiplicity=dict(collections.Counter(ed.values())),boundary_loops=sorted(bl),source_nonadjacent_intersecting_triangle_pairs=len(hits),example_intersections=sorted(hits)[:16],front_axis='-Y',up_axis='+Z',z_min=zmin,z_max=zmax,center_x=N,uv_front=.5,uv_back=[0,1],sleeve_faces=sleeve_faces,collar_faces=collar_faces)
(OUT/'geometry.json').write_text(json.dumps(info,indent=2))
print('COAT_QA', {k:v for k,v in info.items() if not k.endswith('_faces')})
