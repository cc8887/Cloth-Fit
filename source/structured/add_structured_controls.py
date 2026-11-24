"""Install V4 interactive source profile controls on the styled Blender mesh.

blender -b --python add_structured_controls.py -- MATERIALIZED_SCENE.blend OUTPUT.blend
Do not use on solver results. Controls update the editable source silhouette
only. Run structure_coat.py/recheck collision to create a new solver input.
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('scene',type=Path)
P.add_argument('output',type=Path)
P.add_argument('--data',type=Path,default=Path(__file__).with_name('structured_controls.json'))
a=P.parse_args(sys.argv[sys.argv.index('--')+1:])
assert a.scene.resolve()!=a.output.resolve()
d=json.loads(a.data.read_text())
params=d['defaults']
reference=[Vector(p) for p in d['default_v4_positions']]
delta={k:[Vector(p) for p in xx] for k,xx in d['preview_deltas_at_one'].items()}
assert len(reference)==3472 and all(len(q)==len(reference) for q in delta.values())
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
def match(o):
 q=[x.co for x in o.data.vertices]
 off=Vector(tuple(math.fsum(float(a[i])-float(b[i]) for a,b in zip(q,reference))/len(q) for i in range(3)))
 err=max((a-b-off).length for a,b in zip(q,reference))
 return err,off,o
trial=[match(o) for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)==len(reference)]
assert trial,'No V4 source mesh detected.'
err,offset,o=min(trial,key=lambda k:k[0])
assert err<1e-4,f'V4 source order mismatch {err}; will not modify scene.'
assert o.data.shape_keys is None
basis=[p+offset-sum((params[k]*ds[i] for k,ds in delta.items()),Vector((0,0,0))) for i,p in enumerate(reference)]
base=o.shape_key_add(name='Basis · neutral V4 control cage')
for i,p in enumerate(basis):base.data[i].co=p
names={'chest':'Chest Ease · 胸部放量','waist':'Waist Width · 腰身','abdomen':'Abdomen Depth · 腹部','sleeve':'Sleeve Volume · 袖量','hem':'Hem Sweep · 下摆','structure':'Panel Fairing · 挺括整形'}
for k,ds in delta.items():
 key=o.shape_key_add(name=names[k],from_mix=False)
 key.relative_key=base
 key.slider_min=0
 key.slider_max=1 if k=='structure' else .55
 key.value=params[k]
 for i,q in enumerate(basis):key.data[i].co=q+ds[i]
o['source_profile_controls']=json.dumps(params)
o['source_profile_controls_notes']='Default profile recreates actual V4 source; each control is a local preview. For combined edits or solver runs, use structure_coat.py and verify geometry. Panel Fairing changes shape smoothness, not physical fabric stiffness. Garment fit on avatars is separate.'
bpy.context.view_layer.update()
actual=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices
e=max((v.co-p-offset).length for v,p in zip(actual,reference))
assert e<1e-4,e
bpy.context.preferences.filepaths.save_version=0
a.output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()))
print('V4_SHAPE_KEYS_QA',json.dumps({'object':o.name,'source_v4_match_error':err,'default_evaluated_error':e,'shape_keys':list(names.values())},ensure_ascii=False))
