"""Recover the exact isotropic target-to-normalized mapping from corresponding target vertices.

Use only on the solver's untouched target_avatar.obj, not step_avatar_n.obj or a preview rotation.
"""
import argparse,json
from pathlib import Path
import numpy as np
a=argparse.ArgumentParser()
for p in ['original_avatar','normalized_avatar','garment','restored']: a.add_argument(p,type=Path)
p=a.parse_args()
def verts(path):
    return np.array([l.split()[1:4] for l in path.open() if l.startswith("v ")],float)
x,y=verts(p.original_avatar),verts(p.normalized_avatar)
if x.shape!=y.shape: raise SystemExit("avatar shape/order mismatch; refusing to fit transform")
xc,yc=x-x.mean(0),y-y.mean(0)
s=float(np.sum(xc*yc)/np.sum(xc*xc))
t=y.mean(0)-s*x.mean(0)
err=np.linalg.norm(y-(s*x+t),axis=1)
span=float(np.ptp(y,axis=0).max())
if s <= 0 or err.max() > max(span*2e-5,1e-6): raise SystemExit(f"Unexpected residual {err.max():.9g}; did not write output")
with p.restored.open('x') as out:
    for line in p.garment.open():
        if line.startswith("v "):
            f=line.split()
            pos=(np.array(f[1:4],float)-t)/s
            out.write("v "+" ".join(f"{v:.10g}" for v in pos)+(" "+" ".join(f[4:]) if len(f)>4 else "")+"\n")
        else:out.write(line)
print(json.dumps({"target_to_normalized_scale":s,"target_to_normalized_translation":t.tolist(),
                  "max_residual_normalized":float(err.max()),"coordinate_space":"original published avatar OBJ"},indent=2))
